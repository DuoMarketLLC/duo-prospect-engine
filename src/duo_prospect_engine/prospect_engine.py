from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATA_FILE = ROOT / "data" / "mock_businesses.json"
DEFAULT_GOOGLE_MAPS_CSV = ROOT / "data" / "google_maps_sample.csv"
DEFAULT_OUTPUT_DIR = ROOT / "output"
DEFAULT_PROFILE = "cpg_brokerage"
SUPPORTED_PROFILES = {"cpg_brokerage", "trades_bidcloser", "real_estate_agents"}
SUPPORTED_INPUT_SOURCES = {"mock", "google_maps_csv"}


def load_mock_businesses(data_file: Path = DEFAULT_DATA_FILE) -> list[dict[str, Any]]:
    """Load local mock businesses used for the first version of the engine."""
    with data_file.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _parse_int(value: str) -> int | None:
    text = value.strip()
    if not text:
        return None
    try:
        return int(text)
    except ValueError:
        return None


def _parse_float(value: str) -> float | None:
    text = value.strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _resolve_website_url(raw: dict[str, Any]) -> str:
    """Resolve website URL from backward-compatible raw fields."""
    return str(raw.get("website") or raw.get("website_url") or "").strip()


def _default_website_quality(raw: dict[str, Any], website_url: str) -> str:
    """Normalize website quality and enforce minimum quality when a site exists."""
    quality = str(raw.get("website_quality", "")).strip().lower()
    if not quality:
        return "medium" if website_url else "low"
    if website_url and quality in {"low", "weak", "outdated"}:
        return "medium"
    return quality


def infer_selling_products(category: str) -> bool:
    """Infer if a business likely sells products based on category wording."""
    text = category.lower()
    product_signals = {
        "store",
        "shop",
        "market",
        "retail",
        "bakery",
        "restaurant",
        "cafe",
        "food",
        "beverage",
        "boutique",
        "pharmacy",
        "dealer",
        "brand",
    }
    return any(signal in text for signal in product_signals)


def load_google_maps_csv(data_file: Path) -> list[dict[str, Any]]:
    """Load Google Maps-style CSV rows and map them into DUO raw business shape."""
    with data_file.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        required_fields = {
            "business_name",
            "category",
            "website_url",
            "phone",
            "address",
            "city",
            "state",
            "rating",
            "review_count",
        }

        if not reader.fieldnames:
            raise ValueError("CSV is missing a header row.")

        missing = sorted(required_fields - set(reader.fieldnames))
        if missing:
            raise ValueError(f"CSV is missing required columns: {', '.join(missing)}")

        businesses: list[dict[str, Any]] = []
        for row in reader:
            website_url = row.get("website_url", "").strip()
            category = row.get("category", "").strip()
            city = row.get("city", "").strip()
            state = row.get("state", "").strip()
            location = ", ".join(part for part in [city, state] if part) or "Unknown"

            mapped = {
                "business_name": row.get("business_name", "").strip(),
                "industry": category or "Unknown",
                "website": website_url,
                "phone": row.get("phone", "").strip(),
                "location": location,
                "contact_name": "",
                "email": "",
                "website_quality": "medium" if website_url else "low",
                "active_social": False,
                "selling_products": infer_selling_products(category),
                "is_operating": True,
                "google_maps_address": row.get("address", "").strip(),
                "google_maps_rating": _parse_float(row.get("rating", "")),
                "google_maps_review_count": _parse_int(row.get("review_count", "")),
            }
            businesses.append(mapped)

        return businesses


def search_businesses(keyword: str, businesses: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Simple keyword search against name + industry.

    This is intentionally basic so it is easy to understand and improve later.
    """
    query = keyword.lower().strip()

    if not query:
        return businesses

    matches: list[dict[str, Any]] = []
    for business in businesses:
        text = f"{business.get('business_name', '')} {business.get('industry', '')}".lower()
        if query in text:
            matches.append(business)

    if matches:
        return matches

    query_terms = query.split()
    for business in businesses:
        text = f"{business.get('business_name', '')} {business.get('industry', '')}".lower()
        if any(term in text for term in query_terms):
            matches.append(business)
    return matches


def apply_profile_scoring(
    profile: str,
    raw: dict[str, Any],
    keyword: str,
    score: int,
    qualification: dict[str, bool],
) -> tuple[int, str]:
    """Apply profile-specific score boosts and return profile context text."""
    industry = raw.get("industry", "").lower()
    name = raw.get("business_name", "").lower()
    search_text = f"{name} {industry} {keyword.lower()}"

    if profile == "cpg_brokerage":
        if raw.get("selling_products"):
            score += 8
        if raw.get("website_quality", "").lower() in {"high", "modern", "professional"}:
            score += 6
        if qualification["likely_needs_ebroker"]:
            score += 6
        if qualification["likely_needs_plug_play_marketer"]:
            score += 6
        context = "Evaluated under cpg_brokerage profile. Strong product and branding fit for growth support."
    elif profile == "trades_bidcloser":
        if not raw.get("selling_products"):
            score += 6
        if qualification["likely_needs_bidcloser"]:
            score += 8
        if qualification["likely_needs_bidrescue"]:
            score += 8
        if any(term in search_text for term in ["quote", "estimate", "contractor", "service", "remodel"]):
            score += 6
        context = "Evaluated under trades_bidcloser profile. High likelihood of estimate-based sales process."
    elif profile == "real_estate_agents":
        if any(term in search_text for term in ["real estate", "agent", "broker", "listing", "realtor"]):
            score += 10
        if raw.get("active_social"):
            score += 8
        if raw.get("contact_name"):
            score += 6
        if raw.get("phone") and raw.get("email"):
            score += 6
        context = "Evaluated under real_estate_agents profile. Signals suggest conversion depends on personal follow-up."
    else:
        context = f"Evaluated under {profile} profile."

    return score, context


def score_lead(raw: dict[str, Any], keyword: str, profile: str) -> tuple[int, dict[str, bool], str, str]:
    """Score a lead using the rules in lead_scoring.md."""
    score = 0

    website_url = _resolve_website_url(raw)
    has_website = bool(website_url)
    website_quality = _default_website_quality(raw, website_url)

    # Website
    if has_website:
        score += 10
    if website_quality in {"high", "modern", "professional"}:
        score += 10
    elif website_quality in {"low", "weak", "outdated"}:
        score += 3

    # Contactability
    if raw.get("email"):
        score += 10
    if raw.get("phone"):
        score += 5
    if raw.get("contact_name"):
        score += 10

    # Business Activity
    if raw.get("active_social"):
        score += 10
    if raw.get("selling_products"):
        score += 10
    if raw.get("is_operating"):
        score += 10

    industry = raw.get("industry", "").lower()
    name = raw.get("business_name", "").lower()
    search_text = f"{name} {industry} {keyword.lower()}"

    # Service fit flags + scoring
    likely_needs_ebroker = any(term in search_text for term in ["food", "beverage", "cpg", "snack", "brand"])
    likely_needs_plug_play = likely_needs_ebroker or "retail" in search_text
    likely_needs_bidcloser = any(term in search_text for term in ["plumbing", "roof", "contractor", "builder", "trades", "service"])
    likely_needs_bidrescue = likely_needs_bidcloser and any(
        term in search_text for term in ["plumbing", "roof", "deck", "fencing", "remodel", "trades"]
    )

    if likely_needs_ebroker:
        score += 10
    if likely_needs_plug_play:
        score += 10
    if likely_needs_bidcloser:
        score += 10
    if likely_needs_bidrescue:
        score += 10

    # Negative signals
    if raw.get("broken_website"):
        score -= 10
    if not any([has_website, raw.get("email"), raw.get("phone"), raw.get("active_social")]):
        score -= 15

    irrelevant_industries = {"government", "school", "hospital"}
    if industry in irrelevant_industries:
        score -= 25

    qualification = {
        "likely_needs_ebroker": likely_needs_ebroker,
        "likely_needs_bidcloser": likely_needs_bidcloser,
        "likely_needs_bidrescue": likely_needs_bidrescue,
        "likely_needs_plug_play_marketer": likely_needs_plug_play,
    }

    score, profile_context = apply_profile_scoring(profile, raw, keyword, score, qualification)
    score = max(1, min(score, 100))

    if score >= 80:
        priority = "High"
    elif score >= 60:
        priority = "Medium"
    elif score >= 40:
        priority = "Low"
    else:
        priority = "Ignore for now"
    return score, qualification, priority, profile_context


def build_leads(keyword: str, businesses: list[dict[str, Any]], profile: str) -> list[dict[str, Any]]:
    """Build leads in the schema format."""
    leads = []
    for raw in search_businesses(keyword, businesses):
        score, qualification, priority, profile_context = score_lead(raw, keyword, profile)
        website_url = _resolve_website_url(raw)
        has_website = bool(website_url)
        website_quality = _default_website_quality(raw, website_url)

        google_context_bits = []
        if raw.get("google_maps_address"):
            google_context_bits.append(f"Address: {raw['google_maps_address']}.")
        if raw.get("google_maps_rating") is not None:
            google_context_bits.append(f"Rating: {raw['google_maps_rating']}/5.")
        if raw.get("google_maps_review_count") is not None:
            google_context_bits.append(f"Reviews: {raw['google_maps_review_count']}.")
        google_context = " ".join(google_context_bits)

        lead = {
            "business_name": raw.get("business_name", ""),
            "website_url": website_url,
            "industry": raw.get("industry", "Unknown"),
            "location": raw.get("location", "Unknown"),
            "contact_name": raw.get("contact_name", ""),
            "email": raw.get("email", ""),
            "phone": raw.get("phone", ""),
            "has_website": "Yes" if has_website else "No",
            "website_quality": website_quality.title(),
            "active_on_social_media": "Yes" if raw.get("active_social") else "No",
            "selling_products": "Yes" if raw.get("selling_products") else "No",
            "likely_needs_ebroker": "Yes" if qualification["likely_needs_ebroker"] else "No",
            "likely_needs_bidcloser": "Yes" if qualification["likely_needs_bidcloser"] else "No",
            "likely_needs_bidrescue": "Yes" if qualification["likely_needs_bidrescue"] else "No",
            "likely_needs_plug_play_marketer": "Yes" if qualification["likely_needs_plug_play_marketer"] else "No",
            "service_profile": profile,
            "lead_score": score,
            "priority": priority,
            "google_maps_address": raw.get("google_maps_address", ""),
            "google_maps_rating": raw.get("google_maps_rating"),
            "google_maps_review_count": raw.get("google_maps_review_count"),
            "observations": (
                f"Matched keyword '{keyword}'. {profile_context} {google_context}".strip()
            ),
            "why_good_fit": f"Scored {score}/100 based on website, contactability, activity, and service fit.",
        }
        leads.append(lead)

    return leads


def save_json(leads: list[dict[str, Any]], output_file: Path) -> None:
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with output_file.open("w", encoding="utf-8") as handle:
        json.dump(leads, handle, indent=2)


def save_csv(leads: list[dict[str, Any]], output_file: Path) -> None:
    output_file.parent.mkdir(parents=True, exist_ok=True)
    if not leads:
        output_file.write_text("", encoding="utf-8")
        return

    with output_file.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(leads[0].keys()))
        writer.writeheader()
        writer.writerows(leads)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="DUO Prospect Engine (v1)")
    parser.add_argument("keyword", nargs="?", default="", help="Example: 'beverage brand' or 'plumbing company'")
    parser.add_argument("--format", choices=["json", "csv"], default="json", help="Output format")
    parser.add_argument("--output", default="", help="Optional output path")
    parser.add_argument("--profile", choices=sorted(SUPPORTED_PROFILES), default=DEFAULT_PROFILE, help="Service profile")
    parser.add_argument(
        "--input-source",
        choices=sorted(SUPPORTED_INPUT_SOURCES),
        default="mock",
        help="Data source: 'mock' for bundled JSON, 'google_maps_csv' for CSV imports.",
    )
    parser.add_argument(
        "--input-file",
        default="",
        help="Optional input path. In google_maps_csv mode, defaults to data/google_maps_sample.csv.",
    )
    return parser.parse_args()


def _load_input_businesses(input_source: str, input_file: str) -> list[dict[str, Any]]:
    if input_source == "mock":
        data_file = Path(input_file) if input_file else DEFAULT_DATA_FILE
        return load_mock_businesses(data_file)

    if input_source == "google_maps_csv":
        data_file = Path(input_file) if input_file else DEFAULT_GOOGLE_MAPS_CSV
        return load_google_maps_csv(data_file)

    raise ValueError(f"Unsupported input source: {input_source}")


def main() -> None:
    args = parse_args()

    businesses = _load_input_businesses(args.input_source, args.input_file)
    leads = build_leads(args.keyword, businesses, args.profile)

    if args.output:
        output_path = Path(args.output)
    else:
        keyword_slug = args.keyword.replace(" ", "_") if args.keyword else "all"
        output_path = DEFAULT_OUTPUT_DIR / f"leads_{args.input_source}_{keyword_slug}.{args.format}"

    if args.format == "json":
        save_json(leads, output_path)
    else:
        save_csv(leads, output_path)

    print(f"Generated {len(leads)} leads for keyword '{args.keyword}'.")
    print(f"Input source: {args.input_source}")
    print(f"Saved to: {output_path}")


if __name__ == "__main__":
    main()
