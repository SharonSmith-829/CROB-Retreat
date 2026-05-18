#!/usr/bin/env python3
"""Geocode events by ZIP and generate a clustered heatmap with event details.

This script reads the outreach events CSV, looks up lat/lon for each ZIP code,
creates a geocoded CSV with `latitude,longitude` columns, and generates
`outreach_heatmap.html` with clustering, popups, and creator toggles.

Usage:
    python geocode_heatmap.py --input "C:\\Users\\sharo\\OneDrive\\Desktop\\Meetings Jan-May 13.csv" --output outreach_heatmap.html
"""
import argparse
import os
import sys

import pandas as pd
import pgeocode
import folium
from folium.plugins import HeatMap, MarkerCluster
from branca.element import MacroElement, Template
import json
import urllib.request
import math
import re


def _close_ring(coords):
    if not coords:
        return coords
    if coords[0] != coords[-1]:
        coords = coords + [coords[0]]
    return coords


def polygon_centroid(coords):
    """Compute centroid (lon, lat) of a single linear ring polygon using planar formula.

    coords: list of [lon, lat]
    Returns (lat, lon)
    """
    coords = _close_ring(coords)
    A = 0.0
    Cx = 0.0
    Cy = 0.0
    for i in range(len(coords) - 1):
        x0, y0 = coords[i]
        x1, y1 = coords[i + 1]
        cross = x0 * y1 - x1 * y0
        A += cross
        Cx += (x0 + x1) * cross
        Cy += (y0 + y1) * cross
    A *= 0.5
    if abs(A) < 1e-12:
        # Degenerate polygon — fall back to average
        xs = [c[0] for c in coords[:-1]]
        ys = [c[1] for c in coords[:-1]]
        return float(sum(ys) / len(ys)), float(sum(xs) / len(xs))
    Cx = Cx / (6.0 * A)
    Cy = Cy / (6.0 * A)
    # Cx is lon, Cy is lat
    return float(Cy), float(Cx)


def geometry_centroid(geom):
    """Compute centroid from GeoJSON geometry object. Returns (lat, lon) or (None,None)."""
    if not geom:
        return None, None
    t = geom.get('type')
    if t == 'Polygon':
        # use exterior ring (first)
        rings = geom.get('coordinates', [])
        if not rings:
            return None, None
        exterior = rings[0]
        # coords are [lon, lat]
        return polygon_centroid(exterior)
    if t == 'MultiPolygon':
        polys = geom.get('coordinates', [])
        total_area = 0.0
        sum_lat = 0.0
        sum_lon = 0.0
        for poly in polys:
            if not poly:
                continue
            exterior = poly[0]
            coords = _close_ring(exterior)
            # estimate signed area in lon/lat planar
            A = 0.0
            for i in range(len(coords) - 1):
                x0, y0 = coords[i]
                x1, y1 = coords[i + 1]
                A += (x0 * y1 - x1 * y0)
            A *= 0.5
            if abs(A) < 1e-12:
                continue
            lat_c, lon_c = polygon_centroid(exterior)
            total_area += abs(A)
            sum_lat += lat_c * abs(A)
            sum_lon += lon_c * abs(A)
        if total_area == 0:
            return None, None
        return float(sum_lat / total_area), float(sum_lon / total_area)
    return None, None


def geocode_zip(zip_code, nomi):
    try:
        if pd.isna(zip_code):
            return None, None
        z = str(int(float(zip_code))) if not isinstance(zip_code, str) else zip_code
        res = nomi.query_postal_code(z)
        if pd.isna(res.latitude) or pd.isna(res.longitude):
            return None, None
        return float(res.latitude), float(res.longitude)
    except Exception:
        return None, None


def _read_csv_robust(path):
    with open(path, 'r', encoding='utf-8') as fh:
        all_lines = [l.rstrip('\n') for l in fh]
    # skip leading/trailing blank lines
    lines = [l for l in all_lines if l.strip() != '']
    if not lines:
        return pd.DataFrame()
    header = lines[0]
    cols = header.split(',')
    ncols = len(cols)
    rows = []
    for line in lines[1:]:
        parts = line.split(',', ncols - 1)
        if len(parts) < ncols:
            parts += [''] * (ncols - len(parts))
        rows.append(parts)
    return pd.DataFrame(rows, columns=cols)


def make_heatmap_from_file(inp, out_html, lat_col='latitude', lon_col='longitude', zip_geojson=None):
    # Read the CSV and normalize whichever header variant it uses.
    df = pd.read_csv(inp, dtype=str, keep_default_na=False, encoding='cp1252')
    column_aliases = {
        'Quorum ID': 'QuorumID',
        'Note Start Date': 'NoteStartDate',
        'Note Created Date': 'NoteCreatedDate',
        'Interaction Type': 'InteractionType',
        'Creator First Name': 'CreatorFirstName',
        'Creator Last Name': 'CreatorLastName',
        'Number of Attendees/ Views': 'AttendeesOrViews',
        'Zip Code of Interaction': 'ZipCode',
        'Did you integrate a survey for this interaction?': 'SurveyIntegrated',
        'Is this event open to the public or is this a private event for invited guests only?': 'PublicOrPrivate',
    }
    df = df.rename(columns={source: target for source, target in column_aliases.items() if source in df.columns})

    for required in ('ZipCode', 'CreatorFirstName', 'CreatorLastName', 'InteractionType', 'NoteStartDate', 'Organizations', 'Topic', 'AttendeesOrViews'):
        if required not in df.columns:
            df[required] = ''

    # Clean up creator names so layer toggles are readable.
    df['CreatorFirstName'] = df['CreatorFirstName'].astype(str).str.strip().str.strip('"')
    df['CreatorLastName'] = df['CreatorLastName'].astype(str).str.strip().str.strip('"')
    df['ZipCode'] = df['ZipCode'].astype(str).str.strip()

    # Use the ZIP code directly.
    df['extracted_zip'] = df['ZipCode']
    
    # Geocode ZIPs
    nomi = pgeocode.Nominatim('us')
    lats = []
    lons = []
    geojson_path = zip_geojson or os.environ.get('ZIP_GEOJSON')
    features_map = {}
    if geojson_path:
        try:
            if geojson_path.startswith('http'):
                with urllib.request.urlopen(geojson_path) as resp:
                    gj = json.load(resp)
            else:
                with open(geojson_path, 'r', encoding='utf-8') as fh:
                    gj = json.load(fh)
            for feat in gj.get('features', []):
                props = feat.get('properties', {})
                for key in ('ZIPCODE', 'ZIP', 'ZCTA5CE10', 'zip'):
                    if key in props and props.get(key) is not None:
                        zipk = str(props.get(key)).strip()
                        latc, lonc = geometry_centroid(feat.get('geometry'))
                        if latc is not None:
                            features_map[zipk] = (latc, lonc)
                        break
        except Exception:
            features_map = {}
    
    for z in df['extracted_zip'].fillna(''):
        lat = lon = None
        zs = str(z).strip()
        if zs and features_map:
            if zs in features_map:
                lat, lon = features_map[zs]
            else:
                try:
                    zs5 = zs.zfill(5)
                    if zs5 in features_map:
                        lat, lon = features_map[zs5]
                except Exception:
                    pass
        if lat is None:
            lat, lon = geocode_zip(z, nomi)
        lats.append(lat)
        lons.append(lon)
    
    df[lat_col] = lats
    df[lon_col] = lons
    geocoded_csv = os.path.splitext(inp)[0] + '_geocoded.csv'
    df.to_csv(geocoded_csv, index=False)
    print(f'Wrote geocoded CSV: {geocoded_csv}')
    
    # Filter to rows with valid coordinates
    coords_df = df.dropna(subset=[lat_col, lon_col])
    if coords_df.empty:
        raise ValueError('No valid coordinates found after geocoding')
    
    # Create map focused on California
    # CA center approximately at (36.7, -119.0)
    m = folium.Map(location=[36.7, -119.0], zoom_start=7)
    
    # Add heatmap layer
    heat_data = [[float(row[lat_col]), float(row[lon_col])] for _, row in coords_df.iterrows()]
    heatmap_layer = HeatMap(heat_data, radius=15, blur=10, max_zoom=13, name='Heatmap')
    heatmap_layer.add_to(m)
    
    # The clustered layer is the all-events view. Clicking a number expands nearby events.
    all_events_group = folium.FeatureGroup(name='All Events (clustered)', show=True)
    all_events_group.add_to(m)
    marker_cluster = MarkerCluster().add_to(all_events_group)
    
    # Create feature groups per creator for toggling
    creator_groups = {}
    for _, row in coords_df.iterrows():
        lat_val = float(row[lat_col])
        lon_val = float(row[lon_col])
        creator = f"{row.get('CreatorFirstName', '')} {row.get('CreatorLastName', '')}".strip()
        if not creator:
            creator = 'Unknown'
        
        # Create popup text with event details
        interaction_type = row.get('InteractionType', 'Unknown')
        topic = row.get('Topic', 'N/A')
        attendees = row.get('AttendeesOrViews', '0')
        date_str = row.get('NoteStartDate', 'N/A')
        org = row.get('Organizations', 'N/A')
        
        popup_text = f"""
        <b>Event</b><br>
        Type: {interaction_type}<br>
        Date: {date_str}<br>
        Topic: {topic}<br>
        Attendees: {attendees}<br>
        Organization: {org}<br>
        Creator: {creator}
        """
        
        # Create feature group for this creator if not exists
        if creator not in creator_groups:
            creator_groups[creator] = folium.FeatureGroup(name=f'Events by {creator}', show=True)
            creator_groups[creator].add_to(m)
        
        # Add marker to creator group and the all-events cluster
        folium.Marker(
            location=[lat_val, lon_val],
            popup=folium.Popup(popup_text, max_width=300),
            tooltip=f"{interaction_type} - {creator}",
            icon=folium.Icon(color='blue', icon='info-sign')
        ).add_to(creator_groups[creator])
        
        folium.Marker(
            location=[lat_val, lon_val],
            popup=folium.Popup(popup_text, max_width=300),
            tooltip=f"{interaction_type} - {creator}",
            icon=folium.Icon(color='blue', icon='info-sign')
        ).add_to(marker_cluster)

    
    # Add layer control to toggle the heatmap, all events, and each creator.
    folium.LayerControl().add_to(m)

    clear_filters = MacroElement()
    clear_filters._template = Template(
        """
        {% macro script(this, kwargs) %}
        var clearFiltersControl = L.control({position: 'topright'});
        clearFiltersControl.onAdd = function (map) {
            var container = L.DomUtil.create('div', 'leaflet-bar leaflet-control');
            container.style.backgroundColor = 'white';
            container.style.borderRadius = '4px';
            container.style.boxShadow = '0 1px 5px rgba(0, 0, 0, 0.4)';
            container.style.overflow = 'hidden';

            var button = L.DomUtil.create('a', '', container);
            button.href = '#';
            button.title = 'Reset filters';
            button.innerHTML = 'Reset filters';
            button.style.display = 'block';
            button.style.padding = '6px 10px';
            button.style.background = '#2b6cb0';
            button.style.color = 'white';
            button.style.textDecoration = 'none';
            button.style.fontSize = '13px';
            button.style.width = 'auto';
            button.style.minWidth = '110px';
            button.style.height = 'auto';
            button.style.lineHeight = '1.2';
            button.style.whiteSpace = 'nowrap';
            button.style.textAlign = 'center';

            L.DomEvent.disableClickPropagation(container);
            L.DomEvent.on(button, 'click', function (e) {
                L.DomEvent.stop(e);
                // Get all overlay checkboxes and uncheck them all
                var inputs = document.querySelectorAll('.leaflet-control-layers-overlays input[type="checkbox"]');
                inputs.forEach(function (input) {
                    if (input.checked) {
                        input.click();
                    }
                });
            });

            return container;
        };
        clearFiltersControl.addTo({{this._parent.get_name()}});
        {% endmacro %}
        """
    )
    m.add_child(clear_filters)
    
    m.save(out_html)
    print(f'Saved heatmap to {out_html}')



def parse_args():
    p = argparse.ArgumentParser(description='Geocode ZIPs and make heatmap')
    p.add_argument('--input', '-i', required=True, help='Input CSV file with a ZIP column')
    p.add_argument('--output', '-o', default='outreach_heatmap.html', help='Output HTML file')
    p.add_argument('--zip-geojson', help='Optional path or URL to California ZIP boundaries GeoJSON to compute centroids')
    return p.parse_args()


def main():
    args = parse_args()
    if not os.path.exists(args.input):
        print('Input file not found:', args.input)
        sys.exit(1)
    try:
        make_heatmap_from_file(args.input, args.output, zip_geojson=args.zip_geojson)
    except Exception as e:
        print('Error:', e)
        sys.exit(2)


if __name__ == '__main__':
    main()
