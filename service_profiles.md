# Service Profiles

The DUO Prospect Engine supports multiple service profiles.

The base engine remains shared, while each profile can apply profile-specific fit logic and scoring emphasis.

## Core Rule

All profiles use the same lead output schema.

Profile logic can vary by:
- target business types
- fit and disqualifier signals
- score interpretation
- recommended DUO offer

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

Scoring is source-agnostic and can use licensing, website, review/directory, and social/business evidence.

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
