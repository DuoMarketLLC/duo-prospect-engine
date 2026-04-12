# Service Profiles

The DUO Prospect Engine supports multiple service profiles, now powered by a shared ingestion layer.

## Core Rule

All profiles consume the same normalized DUO business schema. Source-specific parsing happens in importers, not scoring logic.

This keeps profile scoring source-agnostic and lets future data connectors plug in without rewriting profile rules.

## Ingestion + profile flow

1. Import source data (mock, Google Maps CSV, standard CSV).
2. Normalize to DUO schema (`business_name`, `industry`, `services`, `review_count`, etc.).
3. Preserve `source`, `source_type`, and `raw_source_payload` for traceability.
4. Run shared search + profile scoring.
5. Export leads with human-readable observations and source context.

## Profiles

### cpg_brokerage
Use for:
- food brands
- beverage brands
- CPG brands
- retail-ready consumer product businesses

Best DUO offers:
- eBroker
- Plug & Play Marketer

### trades_bidcloser (Bid Closer qualification)
Use for estimate-driven trade businesses.

Best-fit trades:

**Tier 1**
- kitchen remodelers
- bathroom remodelers
- cabinet companies
- countertop companies
- flooring companies
- tile contractors

**Tier 2**
- window and door companies
- roofing companies
- deck and patio builders
- painting companies doing larger bid-based jobs
- finish carpentry companies
- closet/garage buildout companies

**Tier 3 / lower priority**
- plumbers
- electricians
- HVAC
- handymen
- service-call-first businesses

Scoring remains source-agnostic and can use licensing, website, review/directory, and social/business evidence from any normalized input source.

Score interpretation:
- 85 to 100 = Prime prospect
- 70 to 84 = Very good prospect
- 55 to 69 = Secondary prospect
- below 55 = Do not prioritize

Best DUO offers:
- BidCloser
- BidRescue

### real_estate_agents
Use for:
- solo agents
- small teams
- brokerages
- real estate professionals

Best DUO offers:
- future real estate offer
- future AI follow-up / conversion tools
