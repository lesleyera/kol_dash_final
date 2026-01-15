# components.py
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from config import COLOR_PRIMARY, GOOGLE_MAPS_API_KEY
from utils import find_col, create_warning_delayed_col, highlight_critical_rows

def kpi_text(label: str, value: str, color: str = COLOR_PRIMARY):
    st.markdown(
        f"""<div style="font-size:0.85rem; color:#666; font-weight:600; margin-bottom:2px;">{label}</div>
        <div style="font-size:2.0rem; font-weight:800; color:{color}; line-height:1.1;">{value}</div>""", 
        unsafe_allow_html=True
    )

def render_google_map(df_master, area_filter=None):
    api_key = GOOGLE_MAPS_API_KEY
    lat_col = find_col(df_master, ["Latitude"])
    lon_col = find_col(df_master, ["Longitude"])
    if not lat_col or not lon_col: return "<div>No GPS Data</div>"
    # ... (기존 맵 렌더링 스크립트)

def render_kol_info_box(kol_name: str, df_master: pd.DataFrame, df_contract: pd.DataFrame):
    info = df_master[df_master["Name"] == kol_name].head(1)
    if info.empty: return
    row = info.iloc[0]
    
    # [수정] 사진 추가 (프로필 이미지)
    img_url = f"https://your-server.com/photos/{kol_name}.png"
    
    st.markdown(f"""
    <div style="background:#ffffff; padding:25px; border-radius:15px; border:1px solid #eee; box-shadow:0 2px 10px rgba(0,0,0,0.05);">
        <div style="display:flex; align-items:center;">
            <img src="{img_url}" onerror="this.src='https://via.placeholder.com/100?text={kol_name}';" 
                 style="width:100px; height:100px; border-radius:50%; object-fit:cover; margin-right:30px; border:3px solid #f0f2f6;">
            <div style="flex:1;">
                <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap:15px;">
                    <div><small style="color:#888;">Name</small><div style="font-weight:700;">{kol_name}</div></div>
                    <div><small style="color:#888;">Country</small><div style="font-weight:700;">{row.get('Country','-')}</div></div>
                    <div><small style="color:#888;">Tier</small><div style="font-weight:700;">{row.get('Tier','-')}</div></div>
                    <div><small style="color:#888;">Serial No.</small><div style="font-weight:700;">{row.get('Serial No.','-')}</div></div>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_kol_detail_admin(kol_name: str, df_master: pd.DataFrame, df_contract: pd.DataFrame, df_activity: pd.DataFrame):
    render_kol_info_box(kol_name, df_master, df_contract)
    log = df_activity[df_activity["Name"] == kol_name].copy()
    if not log.empty:
        log = log.sort_values(by="Date", ascending=False)
        log["Date"] = log["Date"].dt.strftime("%Y-%m-%d")
        log["Warning/Delayed"] = log.apply(create_warning_delayed_col, axis=1)
        st.dataframe(log[["Status_norm", "Date", "Task", "Activity", "Warning/Delayed"]].style.apply(highlight_critical_rows, axis=1), use_container_width=True, hide_index=True)