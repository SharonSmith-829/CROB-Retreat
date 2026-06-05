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
from folium.plugins import HeatMap, MarkerCluster
from branca.element import MacroElement, Template


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
    center = [36.7, -119.0]
    m = folium.Map(location=center, zoom_start=start_zoom)

    # Optional heat overlay, kept hidden by default to preserve the older marker-focused look.
    heat_fg = folium.FeatureGroup(name='Heatmap', show=False)
    HeatMap(data=coords.values.tolist(), radius=radius, blur=blur).add_to(heat_fg)
    heat_fg.add_to(m)

    # All events cluster.
    all_events_group = folium.FeatureGroup(name='All Events (clustered)', show=True)
    all_events_group.add_to(m)
    marker_cluster = MarkerCluster().add_to(all_events_group)

    creator_groups = {}
    for _, row in coords.join(df.drop(columns=[lat_col, lon_col], errors='ignore')).iterrows():
        try:
            lat_val = float(row[lat_col])
            lon_val = float(row[lon_col])
        except Exception:
            continue

        creator = f"{_clean_text(row.get('CreatorFirstName', ''))} {_clean_text(row.get('CreatorLastName', ''))}".strip()
        if not creator:
            creator = 'Unknown'

        interaction_type = _clean_text(row.get('InteractionType')) or 'Unknown'
        topic = _clean_text(row.get('Topic')) or 'N/A'
        attendees = _clean_text(row.get('AttendeesOrViews')) or '0'
        date_str = _clean_text(row.get('NoteStartDate')) or 'N/A'
        org = _clean_text(row.get('Organizations')) or 'N/A'
        text = _clean_text(row.get('Text'))
        if len(text) > 220:
            text = text[:217] + '...'

        popup_text = f"""
        <b>Event</b><br>
        Type: {interaction_type}<br>
        Date: {date_str}<br>
        Topic: {topic}<br>
        Attendees: {attendees}<br>
        Organization: {org}<br>
        Creator: {creator}<br>
        {text}
        """

        if creator not in creator_groups:
            creator_groups[creator] = folium.FeatureGroup(name=f'Events by {creator}', show=True)
            creator_groups[creator].add_to(m)

        icon = folium.Icon(color='blue', icon='info-sign')
        folium.Marker(
            location=[lat_val, lon_val],
            popup=folium.Popup(popup_text, max_width=320),
            tooltip=f"{interaction_type} - {creator}",
            icon=icon,
        ).add_to(creator_groups[creator])

        folium.Marker(
            location=[lat_val, lon_val],
            popup=folium.Popup(popup_text, max_width=320),
            tooltip=f"{interaction_type} - {creator}",
            icon=icon,
        ).add_to(marker_cluster)

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
