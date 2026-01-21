# components.py
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from config import COLOR_PRIMARY, COLOR_NAVY, GOOGLE_MAPS_API_KEY
from utils import find_col, create_warning_delayed_col, highlight_critical_rows

def kpi_text(label: str, value: str, color: str = COLOR_PRIMARY):
    st.markdown(
        f"""
        <div style="font-size:0.85rem; color:#666; font-weight:600; margin-bottom:2px; font-family:'Inter';">{label}</div>
        <div style="font-size:2.0rem; font-weight:800; color:{color}; line-height:1.1; font-family:'Inter';">{value}</div>
        """, unsafe_allow_html=True
    )

def render_google_map(df_master, area_filter=None):
    api_key = GOOGLE_MAPS_API_KEY
    lat_col = find_col(df_master, ["lat", "latitude", "Latitude"])
    lon_col = find_col(df_master, ["lon", "longitude", "Longitude"])
    if lat_col is None or lon_col is None: return "<div style='padding:8px;'>No location data available.</div>"

    df_map = df_master.dropna(subset=[lat_col, lon_col]).copy()
    if area_filter and area_filter != "All": df_map = df_map[df_map["Area"] == area_filter]
    
    if df_map.empty:
        map_center_lat, map_center_lng = 37.5665, 126.9780
        markers_json = "[]"
    else:
        df_map["Latitude_Raw"] = pd.to_numeric(df_map[lat_col], errors="coerce")
        df_map["Longitude_Raw"] = pd.to_numeric(df_map[lon_col], errors="coerce")
        df_map = df_map.dropna(subset=["Latitude_Raw", "Longitude_Raw"])
        
        df_map["Latitude"] = df_map["Latitude_Raw"]
        df_map["Longitude"] = df_map["Longitude_Raw"]
        
        map_center_lat = df_map["Latitude"].mean()
        map_center_lng = df_map["Longitude"].mean()

        markers_list = []
        for _, row in df_map.iterrows():
            name = row.get("Name", "Unknown")
            info_content = f"<b>{name}</b><br>{row.get('Hospital','')}"
            markers_list.append({"name": name, "lat": float(row["Latitude"]), "lng": float(row["Longitude"]), "info": info_content})
        import json as _json
        markers_json = _json.dumps(markers_list)

    html_code = f"""
    <!DOCTYPE html><html><head><style>#map {{ height: 100%; width: 100%; border-radius: 12px; }} html, body {{ height: 100%; margin: 0; padding: 0; }}</style></head>
    <body><div id="map"></div><script>
    function initMap() {{
        const map = new google.maps.Map(document.getElementById("map"), {{ zoom: {2 if area_filter == 'All' else 4}, center: {{ lat: {map_center_lat}, lng: {map_center_lng} }}, mapTypeControl: false, streetViewControl: false }});
        const markersData = {markers_json};
        const infoWindow = new google.maps.InfoWindow();
        markersData.forEach((data) => {{
            const marker = new google.maps.Marker({{ position: {{ lat: data.lat, lng: data.lng }}, map: map, title: data.name }});
            marker.addListener("click", () => {{ infoWindow.setContent(data.info); infoWindow.open(map, marker); }});
        }});
    }}</script><script src="https://maps.googleapis.com/maps/api/js?key={api_key}&callback=initMap" async defer></script></body></html>
    """
    return html_code

def render_kol_info_box(kol_name: str, df_master: pd.DataFrame, df_contract: pd.DataFrame):
    info = df_master[df_master["Name"] == kol_name].head(1)
    contract_info = df_contract[df_contract["Name"] == kol_name].copy()
    
    contract_period_str = "-"
    contract_times_str = "-"
    if not contract_info.empty:
        start_date = contract_info["Contract_Start"].min()
        end_date = contract_info["Contract_End"].max()
        if pd.notna(start_date) and pd.notna(end_date):
            contract_period_str = f"{start_date.strftime('%Y.%m.%d')} ~ {end_date.strftime('%Y.%m.%d')}"
        times_list = contract_info["Times"].dropna().astype(str).unique().tolist()
        if times_list: contract_times_str = ", ".join(times_list)

    area = info.iloc[0]["Area"] if not info.empty else "-"
    country = info.iloc[0]["Country"] if not info.empty else "-"
    scanner = info.iloc[0]["Delivered_Scanner"] if not info.empty else "-"
    serial_no = info.iloc[0]["Serial_No"] if not info.empty else "-"
    photo_url = info.iloc[0]["Photo"] if not info.empty else "-"
    
    notion_url = info.iloc[0]["Notion_Link"] if not info.empty else None
    pdf_url = info.iloc[0]["PDF_Link"] if not info.empty else None 

    if pdf_url and str(pdf_url).startswith("http"):
        pdf_btn_html = f'<a href="{pdf_url}" target="_blank" style="text-decoration:none; background:{COLOR_PRIMARY}; color:white; padding:8px 16px; border-radius:6px; margin-right:10px; font-size:0.85rem; display:inline-block;">📂 Open PDF</a>'
    else:
        pdf_btn_html = '<span style="color:#ccc; font-size:0.85rem; margin-right:10px;">📂 No PDF</span>'

    if notion_url and str(notion_url).startswith("http"):
        notion_btn_html = f'<a href="{notion_url}" target="_blank" style="text-decoration:none; background:#474747; color:white; padding:8px 16px; border-radius:6px; font-size:0.85rem; display:inline-block;">🔗 Notion Page</a>'
    else:
        notion_btn_html = '<span style="color:#ccc; font-size:0.85rem;">🔗 No Notion</span>'

    c1, c2 = st.columns([1, 4])
    with c1:
        if photo_url and str(photo_url).startswith("http"):
            st.image(photo_url, use_container_width=True)
        else:
            st.markdown('<div style="width:100%; height:150px; background:#f3f4f6; border-radius:8px; display:flex; align-items:center; justify-content:center; color:#9ca3af;">No Photo</div>', unsafe_allow_html=True)
            
    with c2:
        html_content = f"""
        <div class="info-box" style="margin-top:0; width:100%; max-width:none; box-sizing: border-box;">
            <div style="display:flex; justify-content: space-between; flex-wrap: wrap; margin-bottom: 20px; width:100%;">
                <div style="flex:1; min-width:120px; margin-right:10px;">
                    <div class="info-label" style="font-size:0.75rem; color:#666; font-weight:600;">Name</div>
                    <div class="info-val" style="font-size:1.1rem; font-weight:700;">{kol_name}</div>
                </div>
                <div style="flex:1; min-width:100px; margin-right:10px;">
                    <div class="info-label" style="font-size:0.75rem; color:#666; font-weight:600;">Region</div>
                    <div class="info-val" style="font-size:1.1rem; font-weight:700;">{area}</div>
                </div>
                <div style="flex:1; min-width:100px; margin-right:10px;">
                    <div class="info-label" style="font-size:0.75rem; color:#666; font-weight:600;">Country</div>
                    <div class="info-val" style="font-size:1.1rem; font-weight:700;">{country}</div>
                </div>
                <div style="flex:1.5; min-width:180px; margin-right:10px;">
                    <div class="info-label" style="font-size:0.75rem; color:#666; font-weight:600;">Contract Period</div>
                    <div class="info-val" style="font-size:1.1rem; font-weight:700;">{contract_period_str}</div>
                </div>
                <div style="flex:1; min-width:120px;">
                    <div class="info-label" style="font-size:0.75rem; color:#666; font-weight:600;">Contract Type</div>
                    <div class="info-val" style="font-size:1.1rem; font-weight:700; color:{COLOR_PRIMARY}">{contract_times_str}</div>
                </div>
            </div>
            <div style="display:flex; justify-content: flex-start; flex-wrap: wrap; margin-bottom: 20px; border-top: 1px dashed #eee; padding-top: 15px; width:100%;">
                <div style="margin-right:60px;">
                    <div class="info-label" style="font-size:0.75rem; color:#666; font-weight:600;">Delivered Scanner</div>
                    <div class="info-val" style="font-size:1rem; font-weight:600;">{scanner}</div>
                </div>
                <div style="margin-right:60px;">
                    <div class="info-label" style="font-size:0.75rem; color:#666; font-weight:600;">Serial No.</div>
                    <div class="info-val" style="font-size:1rem; font-weight:600;">{serial_no}</div>
                </div>
            </div>
            <div style="padding-top:15px; border-top:1px solid #eee; width:100%;">
                {pdf_btn_html} {notion_btn_html}
            </div>
        </div>
        """
        st.markdown(html_content, unsafe_allow_html=True)

def render_kol_detail_admin(kol_name: str, df_master: pd.DataFrame, df_contract: pd.DataFrame, df_activity: pd.DataFrame):
    render_kol_info_box(kol_name, df_master, df_contract)
    st.markdown('<div class="section-title">Contract Progress Rates</div>', unsafe_allow_html=True)
    
    log = df_activity[df_activity["Name"] == kol_name].copy()
    if not log.empty:
        log = log.sort_values(by=["Status_norm", "Date"], ascending=[True, False])
        log["Date"] = log["Date"].dt.strftime("%Y-%m-%d")
        log["Warning/Delayed"] = log.apply(create_warning_delayed_col, axis=1)
        cols_req = ["Status_norm", "Date", "Task", "Activity", "Warning/Delayed"]
        cols_disp = [c for c in cols_req if c in log.columns]
        
        height_val = (len(log) + 1) * 35 + 3
        st.dataframe(
            log[cols_disp].rename(columns={"Status_norm": "Status", "Warning/Delayed": "Delayed"}).style.apply(highlight_critical_rows, axis=1),
            use_container_width=True, hide_index=True,
            height=height_val
        )
