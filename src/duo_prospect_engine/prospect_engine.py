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

TIER_1_TRADES = {
    "kitchen remodeler",
    "bathroom remodeler",
    "cabinet",
    "countertop",
    "flooring",
    "tile contractor",
}
TIER_2_TRADES = {
    "window",
    "door",
    "roofing",
    "deck",
    "patio",
    "painting",
    "finish carpentry",
    "closet",
    "garage buildout",
}
TIER_3_TRADES = {"plumber", "electrician", "hvac", "handyman"}


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


def _safe_int(value: Any) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        cleaned = value.strip().replace("$", "").replace(",", "")
        if cleaned.isdigit():
            return int(cleaned)
    return None


def _safe_float(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        cleaned = value.strip().replace("$", "").replace(",", "")
        try:
            return float(cleaned)
        except ValueError:
            return None
    return None


def _as_text_blob(raw: dict[str, Any], keys: list[str]) -> str:
    values: list[str] = []
    for key in keys:
        value = raw.get(key)
        if isinstance(value, list):
            values.extend(str(item) for item in value if item is not None)
        elif value is not None:
            values.append(str(value))
    return " ".join(values).lower()


def _score_trade_fit(raw: dict[str, Any]) -> tuple[int, str]:
    trade_text = _as_text_blob(raw, ["industry", "category", "business_name", "services", "service_lines"])
    if any(term in trade_text for term in TIER_1_TRADES):
        return 20, "Tier 1 trade match."
    if any(term in trade_text for term in TIER_2_TRADES):
        return 12, "Tier 2 trade match."
    if any(term in trade_text for term in TIER_3_TRADES):
        return 5, "Tier 3 trade match."
    if any(term in trade_text for term in ["remodel", "install", "contractor", "builder"]):
        return 8, "General estimate-driven trade match."
    return 0, "Poor fit trade."


def _score_business_size_fit(raw: dict[str, Any]) -> tuple[int, str]:
    revenue = _safe_int(raw.get("annual_revenue") or raw.get("estimated_revenue") or raw.get("revenue"))
    employees = _safe_int(raw.get("employee_count") or raw.get("employees") or raw.get("team_size"))

    ideal_revenue = revenue is not None and 1_000_000 <= revenue <= 5_000_000
    workable_revenue = revenue is not None and 750_000 <= revenue <= 8_000_000
    ideal_employees = employees is not None and 5 <= employees <= 15
    workable_employees = employees is not None and 3 <= employees <= 25

    if ideal_revenue and ideal_employees:
        return 15, "Ideal revenue and team size."
    if (ideal_revenue and workable_employees) or (ideal_employees and workable_revenue) or (
        workable_revenue and workable_employees
    ):
        return 10, "Good size fit."
    if revenue is None and employees is None:
        return 5, "Missing size data; plausible by default."
    if (revenue is not None and 500_000 <= revenue <= 10_000_000) or (employees is not None and 2 <= employees <= 40):
        return 5, "Uncertain but plausible size fit."
    return 2, "Very small/large or poor size fit."


def _score_sales_model_fit(raw: dict[str, Any]) -> tuple[int, str]:
    text = _as_text_blob(raw, ["industry", "services", "service_lines", "website_text", "description", "offerings"])
    avg_job_size = _safe_float(raw.get("avg_job_size") or raw.get("average_job_size"))

    quote_signals = sum(
        1
        for term in ["estimate", "quote", "project", "remodel", "installation", "design-build", "portfolio", "gallery"]
        if term in text
    )
    service_call_signals = sum(
        1
        for term in ["emergency", "24/7", "repair", "dispatch", "service call", "same day", "cheap", "low-cost"]
        if term in text
    )

    if avg_job_size is not None and 7_500 <= avg_job_size <= 30_000 and quote_signals >= 2 and service_call_signals == 0:
        return 20, "Strongly quote/project based sales model."
    if quote_signals >= 2 and service_call_signals <= 1 and (avg_job_size is None or avg_job_size >= 3_000):
        return 20, "Strong quote-based evidence from public signals."
    if quote_signals >= 1 and service_call_signals <= 2:
        return 12, "Mixed project and service-call signals."
    if quote_signals == 0 and service_call_signals == 0:
        return 6, "Sales model unclear."
    return 2, "Mostly service-call/dispatch/commodity model."


def _score_pain_fit(raw: dict[str, Any]) -> tuple[int, str]:
    text = _as_text_blob(raw, ["reviews_summary", "description", "website_text", "sales_notes", "observation_notes"])
    explicit_flags = sum(
        1
        for key in [
            "price_objection_pressure",
            "bid_match_requests",
            "scope_comparison_friction",
            "owner_led_estimator_process",
            "discount_pressure",
        ]
        if raw.get(key)
    )
    inferred_signals = sum(
        1
        for term in ["cheaper", "match bid", "compare quote", "scope", "follow-up", "discount", "estimate process"]
        if term in text
    )
    total_signals = explicit_flags + inferred_signals
    if total_signals >= 4:
        return 20, "Strong Bid Closer pain-fit evidence."
    if total_signals >= 2:
        return 12, "Moderate pain-fit evidence."
    if total_signals == 1:
        return 5, "Weak pain-fit evidence."
    return 0, "Little pain-fit evidence found."


def _score_professional_maturity(raw: dict[str, Any]) -> tuple[int, str]:
    score = 0
    website_quality = str(raw.get("website_quality", "")).lower()
    review_count = _safe_int(raw.get("review_count") or raw.get("google_maps_review_count"))
    years = _safe_int(raw.get("years_in_business"))

    if raw.get("website"):
        score += 3
    if website_quality in {"high", "modern", "professional"}:
        score += 4
    elif website_quality in {"medium", "decent"}:
        score += 2
    if (review_count or 0) >= 50:
        score += 3
    elif (review_count or 0) >= 15:
        score += 2
    if (years or 0) >= 5:
        score += 2
    elif (years or 0) >= 2:
        score += 1
    if raw.get("active_social"):
        score += 2
    if raw.get("is_operating", True):
        score += 1

    if score >= 12:
        return 15, "Strong presence, reputation, and active business signals."
    if score >= 8:
        return 10, "Decent professional maturity signals."
    if score >= 3:
        return 4, "Weak but present maturity signals."
    return 0, "Poor or incomplete public presence."


def _score_growth_investability(raw: dict[str, Any]) -> tuple[int, str]:
    text = _as_text_blob(raw, ["website_text", "social_activity", "description", "growth_notes"])
    cues = 0
    cues += int(bool(raw.get("active_social")))
    cues += int(bool(raw.get("recent_posts")))
    cues += int(bool(raw.get("is_hiring")))
    cues += int(bool(raw.get("has_showroom")))
    cues += int(bool(raw.get("financing_available")))
    cues += int(any(term in text for term in ["new location", "expanding", "hiring", "project spotlight", "before and after"]))

    if cues >= 4:
        return 10, "Strong growth/investability cues."
    if cues >= 2:
        return 6, "Some growth cues."
    if cues == 1:
        return 2, "Weak growth cues."
    return 0, "No meaningful growth cues."


def _disqualifier_adjustment(raw: dict[str, Any]) -> tuple[int, list[str]]:
    text = _as_text_blob(raw, ["industry", "description", "website_text", "services", "service_lines", "business_model"])
    penalties = 0
    notes: list[str] = []

    if any(term in text for term in ["emergency service", "24/7 emergency", "service call first"]):
        penalties -= 15
        notes.append("Disqualifier: mostly emergency/service-call positioning.")
    if any(term in text for term in ["cheap", "lowest price", "budget only", "discount specialist"]):
        penalties -= 10
        notes.append("Disqualifier: strongly low-price branding.")
    if raw.get("license_status") and str(raw.get("license_status")).lower() not in {"active", "current"}:
        penalties -= 15
        notes.append("Disqualifier: questionable or inactive license status.")
    if raw.get("business_model") and "subcontractor only" in str(raw.get("business_model")).lower():
        penalties -= 12
        notes.append("Disqualifier: primarily subcontractor-only model.")
    if raw.get("branch_type") and any(term in str(raw.get("branch_type")).lower() for term in ["corporate", "franchise"]):
        penalties -= 10
        notes.append("Disqualifier: local buying authority unclear.")
    has_presence = any([raw.get("website"), raw.get("phone"), raw.get("active_social"), raw.get("review_count"), raw.get("google_maps_review_count")])
    if not has_presence:
        penalties -= 12
        notes.append("Disqualifier: no meaningful public presence.")
    if raw.get("avg_job_size") is not None and (_safe_float(raw.get("avg_job_size")) or 0) < 1_000:
        penalties -= 8
        notes.append("Disqualifier: mostly tiny-ticket work.")

    return penalties, notes


def _score_trades_bidcloser(raw: dict[str, Any]) -> tuple[int, list[str], bool, bool]:
    breakdown: list[str] = []

    trade_points, trade_note = _score_trade_fit(raw)
    size_points, size_note = _score_business_size_fit(raw)
    sales_points, sales_note = _score_sales_model_fit(raw)
    pain_points, pain_note = _score_pain_fit(raw)
    maturity_points, maturity_note = _score_professional_maturity(raw)
    growth_points, growth_note = _score_growth_investability(raw)
    penalties, disqualifier_notes = _disqualifier_adjustment(raw)

    base_score = trade_points + size_points + sales_points + pain_points + maturity_points + growth_points
    total = max(1, min(base_score + penalties, 100))

    breakdown.extend(
        [
            f"Trade fit {trade_points}/20 - {trade_note}",
            f"Business size fit {size_points}/15 - {size_note}",
            f"Sales model fit {sales_points}/20 - {sales_note}",
            f"Pain-fit evidence {pain_points}/20 - {pain_note}",
            f"Professional maturity {maturity_points}/15 - {maturity_note}",
            f"Growth/investability {growth_points}/10 - {growth_note}",
        ]
    )
    if penalties:
        breakdown.append(f"Disqualifier adjustment {penalties} points.")
        breakdown.extend(disqualifier_notes)

    likely_bidcloser = trade_points >= 8 and sales_points >= 12 and pain_points >= 5
    likely_bidrescue = likely_bidcloser and (pain_points >= 12 or penalties < 0)
    return total, breakdown, likely_bidcloser, likely_bidrescue


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
        text = _as_text_blob(
            business,
            ["business_name", "industry", "category", "description", "services", "service_lines", "website_text"],
        )
        if query in text:
            matches.append(business)

    if matches:
        return matches

    query_terms = query.split()
    for business in businesses:
        text = _as_text_blob(
            business,
            ["business_name", "industry", "category", "description", "services", "service_lines", "website_text"],
        )
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
        score = max(score, 1)
        context = "Evaluated under trades_bidcloser Bid Closer profile."
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
    if profile == "trades_bidcloser":
        trades_score, breakdown, likely_bidcloser, likely_bidrescue = _score_trades_bidcloser(raw)
        qualification = {
            "likely_needs_ebroker": False,
            "likely_needs_bidcloser": likely_bidcloser,
            "likely_needs_bidrescue": likely_bidrescue,
            "likely_needs_plug_play_marketer": False,
        }
        if trades_score >= 85:
            priority = "Prime prospect"
        elif trades_score >= 70:
            priority = "Very good prospect"
        elif trades_score >= 55:
            priority = "Secondary prospect"
        else:
            priority = "Do not prioritize"
        context = "Bid Closer qualification scoring. " + " ".join(breakdown)
        return trades_score, qualification, priority, context

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
            "why_good_fit": f"Scored {score}/100 based on profile-specific fit evidence and available public signals.",
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
