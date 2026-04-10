# Service Profiles

The DUO Prospect Engine should support multiple service profiles.

The engine itself stays the same.

What changes by profile:
- target industries
- fit signals
- scoring emphasis
- recommended DUO offer

## Core Rule

All profiles should use the same base lead structure and general scoring framework.

Each profile adds its own service-specific fit logic.

## Initial Profiles

### cpg_brokerage
Use for:
- food brands
- beverage brands
- CPG brands
- retail-ready consumer product businesses

Best DUO offers:
- eBroker
- Plug & Play Marketer

Key fit signals:
- product-based business
- retail-ready appearance
- weak or growing brand presence
- likely needs outreach, positioning, or retail growth

### trades_bidcloser
Use for:
- remodelers
- roofers
- painters
- railing companies
- concrete contractors
- deck builders
- fencing companies
- kitchen and bath remodelers
- other estimate-based businesses

Best DUO offers:
- BidCloser
- BidRescue

Key fit signals:
- estimate-based selling
- service business
- likely quote/follow-up friction
- likely price objections
- larger ticket jobs
- sales depends on lead response and close rate

### real_estate_agents
Use for:
- solo agents
- small teams
- brokerages
- real estate professionals

Best DUO offers:
- future real estate offer
- future AI follow-up / conversion tools

Key fit signals:
- active listings
- active marketing presence
- lead conversion dependence
- personal brand importance
- likely follow-up and objection handling needs

## Future Rule

The engine should be easy to expand with more profiles later without rewriting the whole system.
