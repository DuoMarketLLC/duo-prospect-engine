# DUO Prospect Engine (v1)

This repository now includes a **simple first working version** of the prospecting engine.

## What it does

- Takes an optional keyword (example: `beverage brand`, `plumbing company`)
- Supports two input modes:
  - `mock` (default): local JSON test data (`data/mock_businesses.json`)
  - `google_maps_csv`: Google Maps-style CSV import (`data/google_maps_sample.csv`)
- Builds leads using the DUO lead schema
- Scores each lead with basic scoring rules from `lead_scoring.md`
- Exports clean output to JSON or CSV

## Project structure

- `run_engine.py` → simple script to run the engine
- `src/duo_prospect_engine/prospect_engine.py` → input loading, search, scoring, schema mapping, and export logic
- `data/mock_businesses.json` → placeholder business dataset for v1
- `data/google_maps_sample.csv` → sample Google Maps-style CSV input
- `output/` → generated lead files

## Quick start

From the repo root:

### 1) Run mock mode (default)

```bash
python run_engine.py "beverage brand" --format json
python run_engine.py "plumbing company" --format csv
```

Optional custom input/output in mock mode:

```bash
python run_engine.py "beverage brand" --input-source mock --input-file data/mock_businesses.json --output output/my_mock_leads.json
```

### 2) Run Google Maps CSV mode

Use the sample file:

```bash
python run_engine.py "beverage" --input-source google_maps_csv --input-file data/google_maps_sample.csv --format json
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

This is intentionally simple and readable so we can improve it in phases. It is a first live-data bridge via CSV import, not direct scraping.
