# main.py
import streamlit as st
import pandas as pd
import datetime
from PIL import Image
import streamlit.components.v1 as components

from config import *
from utils import local_css, create_warning_delayed_col, highlight_critical_rows
from auth import check_password
from data import load_data
from components import kpi_text, render_google_map, render_kol_info_box, render_kol_detail_admin

# 0. Auth & Config
st.set_page_config(page_title="MEDIT KOL Cockpit", page_icon="💎", layout="wide", initial_sidebar_state="collapsed")
if not check_password(): st.stop()
local_css()

# 1. Data Load
df_master, df_contract, df_activity, last_update = load_data()

# 2. Sidebar & Navigation
with st.sidebar:
    # [수정] Admin Board 삭제
    page = st.radio("Navigation", ["Worldwide KOL Status", "Performance Board"])
    st.markdown("---")
    st.caption(f"Last Update: {last_update}")

# 3. Top Filter Layout
st.markdown('<div class="app-header"><div class="app-title">MEDIT KOL Performance Cockpit</div></div>', unsafe_allow_html=True)

c_year, c_month, c_area = st.columns(3)

# [수정] Worldwide KOL Status 페이지일 경우 상단 필터 미표시 (내부 변수만 설정)
if page == "Worldwide KOL Status":
    selected_year = datetime.datetime.now().year
    selected_month_name = "All"
    selected_area = "All"
else:
    with c_year:
        years = sorted(df_activity["Date"].dt.year.unique().tolist(), reverse=True)
        selected_year = st.selectbox("Year", years if years else [2025])
    with c_month:
        selected_month_name = st.selectbox("Month", ["All"] + list(MONTH_NAME_MAP.values()))
    with c_area:
        areas = sorted(df_master["Area"].dropna().unique().tolist())
        selected_area = st.selectbox("Area", ["All"] + areas)

# 4. Page Routing
if page == "Worldwide KOL Status":
    # [수정] 지역별 KOL 수 KPI (USA, Europe, LATAM)
    usa_count = df_master[df_master["Area"].str.upper().str.strip() == "USA"].shape[0]
    eu_count = df_master[df_master["Area"].str.upper().str.strip() == "EUROPE"].shape[0]
    latam_count = df_master[df_master["Area"].str.upper().str.strip() == "LATAM"].shape[0]
    
    k1, k2, k3, k4 = st.columns(4)
    with k1: kpi_text("Total KOLs", f"{len(df_master)}")
    with k2: kpi_text("USA", f"{usa_count}", "#3B82F6")
    with k3: kpi_text("Europe", f"{eu_count}", "#10B981")
    with k4: kpi_text("LATAM", f"{latam_count}", "#F59E0B")

    st.markdown("#### KOL Location Map")
    components.html(render_google_map(df_master, area_filter="All"), height=500)
    
    st.markdown("---")
    # [수정] KOL 상세 정보 필터 및 사진 표시 연동
    st.markdown("#### KOL Information Details")
    all_kol_names = sorted(df_master["Name"].dropna().unique().tolist())
    target_kol = st.selectbox("Select KOL to view Profile & Activity", ["-"] + all_kol_names)
    if target_kol != "-":
        render_kol_detail_admin(target_kol, df_master, df_contract, df_activity)

elif page == "Performance Board":
    # 데이터 필터링 로직
    df_filtered = df_activity[df_activity["Date"].dt.year == selected_year].copy()
    if selected_month_name != "All":
        df_filtered = df_filtered[df_filtered["Date"].dt.month == MONTH_NAME_TO_NUM[selected_month_name]]
    
    # Area 필터 연동
    if selected_area != "All":
        names_in_area = df_master[df_master["Area"] == selected_area]["Name"].tolist()
        df_filtered = df_filtered[df_filtered["Name"].isin(names_in_area)]

    # 리스트 렌더링
    st.markdown("### Monthly Task List")
    
    # [수정] Status 필터 추가
    st.markdown('<div style="margin-bottom:10px;"></div>', unsafe_allow_html=True)
    status_options = ["TBD", "Planned", "On Progress", "Done"]
    selected_status = st.multiselect("Filter by Status", status_options, default=status_options)
    
    df_display = df_filtered[df_filtered["Status_norm"].isin(selected_status)].copy()
    
    if not df_display.empty:
        df_display = df_display.sort_values(by="Date", ascending=True)
        df_display["Date"] = df_display["Date"].dt.strftime("%Y-%m-%d")
        df_display["Warning/Delayed"] = df_display.apply(create_warning_delayed_col, axis=1)
        
        cols_to_show = ["Name", "Status_norm", "Date", "Task", "Activity", "Warning/Delayed"]
        st.dataframe(
            df_display[cols_to_show].style.apply(highlight_critical_rows, axis=1),
            use_container_width=True, hide_index=True
        )
    else:
        st.info("No data found for the selected filters.")