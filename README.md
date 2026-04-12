# DUO Prospect Engine (v1)

This repository includes a working version of the prospecting engine.

## What it does

- Takes an optional keyword (example: `beverage brand`, `kitchen remodeler`)
- Supports two input modes:
  - `mock` (default): local JSON test data (`data/mock_businesses.json`)
  - `google_maps_csv`: Google Maps-style CSV import (`data/google_maps_sample.csv`)
- Builds leads using the DUO lead schema
- Scores each lead by service profile
- Exports clean output to JSON or CSV

## Bid Closer trade scoring (source-agnostic)

The `trades_bidcloser` profile now runs a Bid Closer qualification model scored out of 100 and is intentionally **source-agnostic**.

It evaluates whatever evidence is available (without depending on any single source):
- licensing/registration status and years in business
- website language (`request a quote`, `free estimate`, project pages)
- review/directory reputation and recency proxies
- social/business activity and growth cues
- size and sales-model proxies

Missing fields are handled with graceful defaults so leads still score with partial data.

Category weights:
- Trade fit (20)
- Business size fit (15)
- Sales model fit (20)
- Pain-fit evidence (20)
- Professional maturity (15)
- Growth/investability (10)

Disqualifier penalties are applied when signals indicate emergency-first dispatch, tiny-ticket focus, low-price branding, inactive licensing, or poor public presence.

Interpretation:
- 85–100 = Prime prospect
- 70–84 = Very good prospect
- 55–69 = Secondary prospect
- <55 = Do not prioritize

## Project structure

- `run_engine.py` → simple script to run the engine
- `src/duo_prospect_engine/prospect_engine.py` → input loading, search, scoring, schema mapping, and export logic
- `data/mock_businesses.json` → sample business dataset
- `data/google_maps_sample.csv` → sample Google Maps-style CSV input
- `output/` → generated lead files

## Quick start

From the repo root:

### 1) Run mock mode (default)

```bash
python run_engine.py "beverage brand" --format json
python run_engine.py "kitchen remodeler" --profile trades_bidcloser --format json
```

### 2) Run Google Maps CSV mode

Use the sample file:

```bash
python run_engine.py "remodel" --input-source google_maps_csv --input-file data/google_maps_sample.csv --profile trades_bidcloser --format json
```

Load all rows (no keyword filter):

```bash
python run_engine.py --input-source google_maps_csv --input-file data/google_maps_sample.csv --format csv
```

## Google Maps CSV columns

The `google_maps_csv` import expects these columns:

- `business_name`
- `category`
- `website_url`
- `phone`
- `address`
- `city`
- `state`
- `rating`
- `review_count`

## Notes

The engine is designed to keep scoring resilient to sparse data while allowing richer records from any public-source pipeline.
