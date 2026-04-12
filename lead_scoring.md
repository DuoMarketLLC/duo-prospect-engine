# Lead Scoring Rules

The DUO Prospect Engine scores leads from 1 to 100.

## Profile-specific scoring

### trades_bidcloser (Bid Closer qualification)

This profile is now source-agnostic. It can score evidence from any available public input (Google Maps CSV, licensing data, websites, directories, review content, and social/business activity). Missing fields are handled with graceful fallbacks.

#### Category weights (100 total)

1. **Trade fit (20 points)**
   - Tier 1 trade: 20
   - Tier 2 trade: 12
   - Tier 3 trade: 5
   - Poor-fit trade: 0

2. **Business size fit (15 points)**
   - Ideal size: 15
   - Good size: 10
   - Uncertain but plausible: 5
   - Very small / very large / poor fit: 0 to 3

3. **Sales model fit (20 points)**
   - Strongly project/quote based: 20
   - Mixed model: 12
   - Unclear: 6
   - Mostly service-call/dispatch/commodity: 0 to 3

4. **Pain-fit evidence (20 points)**
   - Strong evidence: 20
   - Moderate evidence: 12
   - Weak evidence: 5
   - Little/no evidence: 0

5. **Professional maturity (15 points)**
   - Strong presence / solid reputation / active business: 15
   - Decent presence: 10
   - Weak presence: 4
   - Poor/incomplete presence: 0

6. **Growth / investability signals (10 points)**
   - Strong growth cues: 10
   - Some cues: 6
   - Weak cues: 2
   - None: 0

#### Disqualifier adjustments

The engine applies penalties when evidence indicates:
- mostly emergency service work
- mostly tiny-ticket work
- strongly low-price branding
- expired/questionable licensing
- no meaningful public presence
- subcontractor-only model
- corporate/franchise branch with unclear local buying authority

#### Score interpretation
- 85 to 100 = Prime prospect
- 70 to 84 = Very good prospect
- 55 to 69 = Secondary prospect
- below 55 = Do not prioritize

## Legacy profiles

### cpg_brokerage and real_estate_agents

These profiles continue to use the original baseline DUO scoring framework (website, contactability, activity, and service-fit signals).
