# CROB-Retreat

## Outreach Heat Map Environment

This repository now includes a minimal Python environment and script to generate an outreach-event heat map from a CSV file you provide.

### 1) Create and activate an environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 2) Prepare your outreach events CSV

Use this header format (a template is included at `data/outreach_events_template.csv`):

```csv
event_name,latitude,longitude,attendance
```

- `event_name`: Any label for the event
- `latitude` / `longitude`: Decimal GPS coordinates
- `attendance`: Optional numeric weight for heat intensity (defaults to `1`)

### 3) Generate the heat map

```bash
python scripts/create_outreach_heatmap.py \
  --input data/outreach_events_template.csv \
  --output outreach_heatmap.html
```

Open `outreach_heatmap.html` in a browser to view the map.
