# DUO Prospect Engine (v1)

This repository now includes a **simple first working version** of the prospecting engine.

## What it does

- Takes a keyword (example: `beverage brand`, `plumbing company`)
- Searches businesses from local mock data (`data/mock_businesses.json`)
- Builds leads using the DUO lead schema
- Scores each lead with basic scoring rules from `lead_scoring.md`
- Exports clean output to JSON or CSV

## Project structure

- `run_engine.py` → simple script to run the engine
- `src/duo_prospect_engine/prospect_engine.py` → search, scoring, schema mapping, and export logic
- `data/mock_businesses.json` → placeholder business dataset for v1
- `output/` → generated lead files

## Quick start

From the repo root:

```bash
python run_engine.py "beverage brand" --format json
python run_engine.py "plumbing company" --format csv
```

Optional custom output path:

```bash
python run_engine.py "beverage brand" --format json --output output/my_leads.json
```

## Notes

This is intentionally simple and readable so we can improve it in phases.
