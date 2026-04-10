# Lead Scoring Rules

The DUO Prospect Engine should score leads from 1 to 100.

## Base Scoring Factors

### Website
- Has website: +10
- Modern / professional website: +10
- Weak / outdated website: +3
- No website: 0

### Contactability
- Public email found: +10
- Public phone found: +5
- Contact name found: +10

### Business Activity
- Active social media presence: +10
- Clear services or products listed: +10
- Evidence business is currently operating: +10

### Service Fit

#### eBroker Fit
Add points if:
- food or beverage brand
- consumer packaged goods brand
- likely seeking retail growth
- product appears retail-ready

#### Plug & Play Marketer Fit
Add points if:
- CPG brand
- weak messaging
- weak positioning
- poor brand presentation
- likely needs marketing structure

#### BidCloser Fit
Add points if:
- estimate-based business
- service business with larger-ticket jobs
- likely dealing with price objections
- likely dependent on follow-up and quote conversion

#### BidRescue Fit
Add points if:
- estimate-based business
- likely losing deals from delay, pressure, or weak follow-up
- small to medium contractor or trade business

## Negative Signals
- Broken website: -10
- No useful business presence found: -15
- Clearly irrelevant business type: -25

## Final Rules
- 80 to 100 = High priority
- 60 to 79 = Medium priority
- 40 to 59 = Low priority
- Under 40 = Ignore for now
