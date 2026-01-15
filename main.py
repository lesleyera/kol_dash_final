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

# 0. Page Config
st.set_page_config(page_title="MEDIT KOL Performance Cockpit", page_icon="💎", layout="wide", initial_sidebar_state="collapsed")
if not check_password(): st.stop()
local_css()

# 1. Data Load (Error handling 추가)
try:
    df_master, df_contract, df_activity, last_update = load_data()
except Exception as e:
    st.error(f"데이터 로드 중 오류가 발생했습니다. 구글 시트 설정을 확인해주세요. ({e})")
    st.stop()

# 2. Navigation
with st.sidebar:
    # [수정] Admin Board 삭제
    page = st.radio("Navigation", ["Worldwide KOL Status", "Performance Board"])
    st.markdown("---")
    st.caption(f"Last Update: {last_update}")

# 3. Top Filter Layout
st.markdown('<div class="app-header"><div class="app-title">MEDIT KOL Performance Cockpit</div></div>', unsafe_allow_html=True)

# [수정] Worldwide KOL Status일 때 상단 필터 삭제를 위해 컬럼 공간 확보만 진행
c_year, c_month, c_area = st.columns(3)

if page == "Worldwide KOL Status":
    # 필터 값을 기본값으로 고정 (UI 미노출)
    selected_year, selected_month_name, selected_area = 2025, "All", "All"
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
    # [수정] KPI: 전체 KOL 수 및 지역별 수 (USA, Europe, LATAM)
    usa_count = df_master[df_master["Area"].str.upper() == "USA"].shape[0]
    eu_count = df_master[df_master["Area"].str.upper() == "EUROPE"].shape[0]
    latam_count = df_master[df_master["Area"].str.upper() == "LATAM"].shape[0]
    
    k1, k2, k3, k4 = st.columns(4)
    with k1: kpi_text("Total KOLs", f"{len(df_master)}")
    with k2: kpi_text("USA", f"{usa_count}", "#3B82F6")
    with k3: kpi_text("Europe", f"{eu_count}", "#10B981")
    with k4: kpi_text("LATAM", f"{latam_count}", "#F59E0B")

    st.markdown("#### KOL Location Map")
    components.html(render_google_map(df_master, area_filter="All"), height=500)
    
    st.markdown("---")
    # [수정] KOL 정보 확인 필터 배치 (기존 Admin Board 기능)
    st.markdown("#### KOL Information Details")
    all_kol_names = sorted(df_master["Name"].dropna().unique().tolist())
    target_kol = st.selectbox("Select KOL Name", ["-"] + all_kol_names)
    if target_kol != "-":
        render_kol_detail_admin(target_kol, df_master, df_contract, df_activity)

elif page == "Performance Board":
    # 데이터 필터링
    df_filtered = df_activity[df_activity["Date"].dt.year == selected_year].copy()
    if selected_month_name != "All":
        df_filtered = df_filtered[df_filtered["Date"].dt.month == MONTH_NAME_TO_NUM[selected_month_name]]
    if selected_area != "All":
        names_in_area = df_master[df_master["Area"] == selected_area]["Name"].tolist()
        df_filtered = df_filtered[df_filtered["Name"].isin(names_in_area)]

    st.markdown("### Monthly All Tasks")
    
    # [수정] Status 필터 추가
    status_options = ["TBD", "Planned", "On Progress", "Done"]
    selected_status = st.multiselect("Filter by Status", status_options, default=status_options)
    
    df_display = df_filtered[df_filtered["Status_norm"].isin(selected_status)].copy()
    
    if not df_display.empty:
        df_display["Date"] = df_display["Date"].dt.strftime("%Y-%m-%d")
        df_display["Warning/Delayed"] = df_display.apply(create_warning_delayed_col, axis=1)
        st.dataframe(
            df_display[["Name", "Status_norm", "Date", "Task", "Activity", "Warning/Delayed"]].style.apply(highlight_critical_rows, axis=1),
            use_container_width=True, hide_index=True
        )
    else:
        st.info("검색 조건에 맞는 데이터가 없습니다.")