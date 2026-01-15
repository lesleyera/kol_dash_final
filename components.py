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
    if area_filter and area_filter != "All":
        df_map = df_map[df_map["Area"] == area_filter]

    markers = ""
    for idx, row in df_map.iterrows():
        markers += f"new google.maps.Marker({{position: {{lat: {row[lat_col]}, lng: {row[lon_col]}}}, map: map, title: '{row['Name']}'}});\n"

    html_code = f"""
    <div id="map" style="height:100%; width:100%; border-radius:12px;"></div>
    <script>
        function initMap() {{
            const map = new google.maps.Map(document.getElementById("map"), {{
                zoom: 2, center: {{lat: 20, lng: 0}},
                styles: [{{ "featureType": "administrative", "elementType": "labels.text.fill", "stylers": [{{ "color": "#444444" }}] }}]
            }});
            {markers}
        }}
    </script>
    <script async defer src="https://maps.googleapis.com/maps/api/js?key={api_key}&callback=initMap"></script>
    """
    return html_code

def render_kol_info_box(kol_name: str, df_master: pd.DataFrame, df_contract: pd.DataFrame):
    info = df_master[df_master["Name"] == kol_name].head(1)
    if info.empty: return
    
    row = info.iloc[0]
    country = row.get("Country", "-")
    area = row.get("Area", "-")
    tier = row.get("Tier", "-")
    serial_no = row.get("Serial No.", "-")
    
    # [수정] KOL 사진 추가 (파일명: Name.png 기준, 없을 시 placeholder)
    img_path = f"https://raw.githubusercontent.com/user-attachments/assets/kol_photos/{kol_name}.png" 
    
    html_content = f"""
    <div class="info-box">
        <div style="display:flex; align-items:flex-start; margin-bottom: 20px;">
            <div style="margin-right:30px;">
                <img src="{img_path}" onerror="this.src='https://via.placeholder.com/120?text=No+Image';" 
                     style="width:120px; height:120px; border-radius:12px; object-fit:cover; border:1px solid #eee;">
            </div>
            <div style="flex:1;">
                <div style="display:flex; justify-content: space-between; flex-wrap: wrap;">
                    <div style="margin-right:20px; margin-bottom:10px;">
                        <div class="info-label">Name</div>
                        <div class="info-val">{kol_name}</div>
                    </div>
                    <div style="margin-right:20px; margin-bottom:10px;">
                        <div class="info-label">Country</div>
                        <div class="info-val">{country} ({area})</div>
                    </div>
                    <div style="margin-right:20px; margin-bottom:10px;">
                        <div class="info-label">Tier</div>
                        <div class="info-val">{tier}</div>
                    </div>
                    <div style="margin-right:20px; margin-bottom:10px;">
                        <div class="info-label">Serial No.</div>
                        <div class="info-val">{serial_no}</div>
                    </div>
                </div>
            </div>
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
        cols_disp = ["Status_norm", "Date", "Task", "Activity", "Warning/Delayed"]
        
        st.dataframe(
            log[cols_disp].style.apply(highlight_critical_rows, axis=1),
            use_container_width=True, hide_index=True
        )
    else:
        st.caption("No activity logs found for this KOL.")