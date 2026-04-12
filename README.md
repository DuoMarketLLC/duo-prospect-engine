# DUO Prospect Engine (v2 ingestion layer)

This repository now includes a **source-agnostic ingestion layer** for Bid Closer and other DUO prospecting workflows.

## What it does

- Accepts input from multiple source formats.
- Normalizes every source into one canonical DUO business schema.
- Preserves source metadata and raw source payload for traceability.
- Runs search + scoring on normalized records (without changing profile logic per source).
- Exports normalized records and lead outputs to JSON/CSV.

## Supported input sources

- `mock` (default): `data/mock_businesses.json`
- `google_maps_csv`: Google Maps-style CSV export (`data/google_maps_sample.csv`)
- `standard_csv`: DUO-friendly normalized flat CSV (`data/standard_businesses_sample.csv`)

## Standard DUO business schema

The normalized ingestion schema includes:

- `business_name`
- `website`
- `phone`
- `email`
- `address`
- `city`
- `state`
- `zip`
- `location`
- `category`
- `industry`
- `services`
- `service_lines`
- `description`
- `review_count`
- `rating`
- `years_in_business`
- `employee_count`
- `estimated_revenue`
- `website_quality`
- `active_social`
- `recent_posts`
- `hiring`
- `has_showroom`
- `licensing_status`
- `source`
- `source_type`
- `raw_source_payload`

Not every source will provide every field. Missing fields are handled gracefully so scoring remains resilient.

## Importer pattern

Current importer functions:

- `import_google_maps_csv(file_path)`
- `import_standard_csv(file_path)`

The ingestion layer is structured so new importers can be added with minimal change to scoring logic, such as:

- Google Places API JSON
- state licensing exports
- directory CSV exports
- VA/manual research CSVs

## Quick start

From repo root:

### 1) Mock mode (backward compatible)

```bash
python run_engine.py "kitchen remodeler" --profile trades_bidcloser --format json
```

### 2) Google Maps CSV ingestion

```bash
python run_engine.py "remodel" \
  --input-source google_maps_csv \
  --input-file data/google_maps_sample.csv \
  --profile trades_bidcloser \
  --export-normalized output/normalized_google_maps.json \
  --format json
```

### 3) Standard CSV ingestion

```bash
python run_engine.py "kitchen" \
  --input-source standard_csv \
  --input-file data/standard_businesses_sample.csv \
  --profile trades_bidcloser \
  --export-normalized output/normalized_standard.csv.json \
  --format csv
```

### 4) Load all rows (no keyword filter)

```bash
python run_engine.py \
  --input-source standard_csv \
  --input-file data/standard_businesses_sample.csv \
  --format json
```

## Traceability in output leads

Each output lead now includes:

- `source`
- `source_type`
- `source_context` (address/location/raw payload context)
- human-readable `observations` with source details

## Project structure

- `run_engine.py` → CLI launcher
- `src/duo_prospect_engine/prospect_engine.py` → ingestion, normalization, scoring, export
- `data/mock_businesses.json` → legacy mock data
- `data/google_maps_sample.csv` → Google Maps sample input
- `data/standard_businesses_sample.csv` → normalized flat CSV sample
- `output/` → generated files
