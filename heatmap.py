#!/usr/bin/env python3
"""Generate a geographic heatmap from outreach events CSV.

Usage example:
  python heatmap.py --input outreach_events.csv --output outreach_heatmap.html
"""
import argparse
import os
import sys

import pandas as pd
import folium
from folium.plugins import HeatMap


def _clean_text(value):
    if pd.isna(value):
        return ''
    text = str(value).strip()
    return '' if text.lower() == 'nan' else text


def make_heatmap(df, output, lat_col='latitude', lon_col='longitude', radius=15, blur=10, start_zoom=10):
    if df.empty:
        raise ValueError('Dataframe is empty')
    coords = df[[lat_col, lon_col]].dropna()
    if coords.empty:
        raise ValueError('No valid coordinate rows found')
    center = [float(coords[lat_col].mean()), float(coords[lon_col].mean())]
    m = folium.Map(location=center, zoom_start=start_zoom)

    # Heatmap layer (base overlay)
    heat_fg = folium.FeatureGroup(name='Heatmap', show=True)
    HeatMap(data=coords.values.tolist(), radius=radius, blur=blur).add_to(heat_fg)
    heat_fg.add_to(m)

    # Add per-person layers with markers
    # Use CreatorFirstName and CreatorLastName if present, else fall back to 'Unknown'
    if 'CreatorFirstName' in df.columns or 'CreatorLastName' in df.columns:
        creators = {}
        for _, row in df.iterrows():
            lat = row.get(lat_col)
            lon = row.get(lon_col)
            if pd.isna(lat) or pd.isna(lon) or str(lat).strip()=='' or str(lon).strip()=='':
                continue
            fname = _clean_text(row.get('CreatorFirstName', ''))
            lname = _clean_text(row.get('CreatorLastName', ''))
            creator = (fname + ' ' + lname).strip() or 'Unknown'
            creators.setdefault(creator, []).append(row)

        for creator, rows in creators.items():
            fg = folium.FeatureGroup(name=creator, show=False)
            for r in rows:
                try:
                    plat = float(r.get(lat_col))
                    plon = float(r.get(lon_col))
                except Exception:
                    continue
                popup_parts = []
                note_date = _clean_text(r.get('NoteStartDate'))
                interaction_type = _clean_text(r.get('InteractionType'))
                organization = _clean_text(r.get('Organizations'))
                text = _clean_text(r.get('Text'))
                if note_date:
                    popup_parts.append(note_date)
                if interaction_type:
                    popup_parts.append(interaction_type)
                if organization:
                    popup_parts.append(organization)
                if text:
                    txt = text
                    if len(txt) > 200:
                        txt = txt[:197] + '...'
                    popup_parts.append(txt)
                popup = '<br/>'.join(popup_parts)
                folium.CircleMarker(location=(plat, plon), radius=5, color='blue', fill=True, fill_opacity=0.7, popup=popup).add_to(fg)
            fg.add_to(m)
    # Add layer control so users can toggle creators
    folium.LayerControl(collapsed=False).add_to(m)
    m.save(output)
    print(f'Saved heatmap to {output}')


def parse_args():
    p = argparse.ArgumentParser(description='Generate outreach events heatmap')
    p.add_argument('--input', '-i', required=True, help='Input CSV file with latitude and longitude columns')
    p.add_argument('--output', '-o', default='outreach_heatmap.html', help='Output HTML file with the map')
    p.add_argument('--lat', default='latitude', help='Latitude column name')
    p.add_argument('--lon', default='longitude', help='Longitude column name')
    p.add_argument('--radius', type=int, default=15, help='Heatmap point radius')
    p.add_argument('--blur', type=int, default=10, help='Heatmap blur')
    p.add_argument('--zoom', type=int, default=10, help='Initial zoom level')
    return p.parse_args()


def main():
    args = parse_args()
    if not os.path.exists(args.input):
        print('Input file not found:', args.input)
        sys.exit(1)
    df = pd.read_csv(args.input)
    try:
        make_heatmap(df, args.output, lat_col=args.lat, lon_col=args.lon, radius=args.radius, blur=args.blur, start_zoom=args.zoom)
    except Exception as e:
        print('Error creating heatmap:', e)
        sys.exit(2)


if __name__ == '__main__':
    main()
