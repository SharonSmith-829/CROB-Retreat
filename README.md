# Outreach Heatmap

This tool generates an interactive geographic heatmap with clustering and event details showing where outreach events occurred.

## Features
- **Heatmap layer**: visualize event density across regions
- **Marker clustering**: events automatically cluster at zoom levels; click clusters to expand
- **Event popups**: hover over or click markers to see event details (type, date, topic, attendees, organization, creator)
- **Creator toggles**: use the layer control (top-right) to show/hide events by creator
- **GeoJSON ZIP boundaries**: converts ZIP codes to accurate polygon centroids (no API key needed)

## Files
- [index.html](index.html) — main entry page with links to the HTML views
- [requirements.txt](requirements.txt) — Python dependencies
- [outreach_events.csv](outreach_events.csv) — your Quorum export data
- [geocode_heatmap.py](geocode_heatmap.py) — main script
- [outreach_events_geocoded.csv](outreach_events_geocoded.csv) — geocoded events (created on first run)
- [outreach_heatmap.html](outreach_heatmap.html) — interactive map (open in browser)
- [outreach_dashboard.html](outreach_dashboard.html) — combined outreach map and distressed ZIP coverage page
- [zip_coverage_analysis.html](zip_coverage_analysis.html) — distressed ZIP analysis tool

## Quick start (Windows PowerShell)

```powershell
python -m venv .venv
.\\.venv\\Scripts\\Activate.ps1
pip install -r requirements.txt
python geocode_heatmap.py --input outreach_events.csv --output outreach_heatmap.html --zip-geojson "C:\path\to\USA_ZIP_Code_Areas.geojson"
```

## Using the map
- **Zoom in/out** to see clustering details
- **Toggle layers** using the layer control (top-right checkbox):
  - Check/uncheck "Heatmap" to show/hide density overlay
  - Check/uncheck "Clustered Events" to show/hide individual markers
  - Check/uncheck "Events by [Creator Name]" to filter by person
- **Hover** over a marker to see a tooltip with interaction type and creator
- **Click** a marker to see a popup with full event details

## Options
```
--input, -i          Input CSV file with outreach data (required)
--output, -o         Output HTML file (default: outreach_heatmap.html)
--zip-geojson        Path or URL to ZIP boundary GeoJSON for accurate centroids
```

If you don't provide `--zip-geojson`, the script will fall back to ZIP centroid lookup via `pgeocode`.

## Next steps
- Open [index.html](index.html) first, then click the page you want
- Replace `outreach_events.csv` with your real data
- Customize marker colors, clustering behavior, or heatmap intensity as needed
- Open `outreach_dashboard.html` to review both views in one place and share the page from GitHub

