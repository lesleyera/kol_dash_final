# app.py
import streamlit as st
import pandas as pd
import datetime
from PIL import Image
import streamlit.components.v1 as components
from streamlit_calendar import calendar as st_calendar

# Modules
from config import *
from utils import local_css, create_warning_delayed_col, highlight_critical_rows
from auth import check_password
from data import load_data
from components import kpi_text, render_google_map, render_kol_info_box

# -----------------------------------------------------------------
# 0. Auth & Page Config
# -----------------------------------------------------------------
try:
    logo_image = Image.open("image_0.png")
    st.set_page_config(
        page_title="MEDIT KOL Performance Cockpit",
        page_icon="💎",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
except FileNotFoundError:
    st.set_page_config(
        page_title="MEDIT KOL Performance Cockpit",
        page_icon="💎",
        layout="wide",
        initial_sidebar_state="collapsed",
    )

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not check_password():
    st.stop()

# -----------------------------------------------------------------
# 1. CSS & Data Load
# -----------------------------------------------------------------
local_css()

df_master, df_contract, df_activity = load_data(
    FILE_SETTINGS["MASTER_TAB"], FILE_SETTINGS["CONTRACT_TAB"], FILE_SETTINGS["ACTIVITY_TAB"]
)

if df_master is None: st.stop()

# -----------------------------------------------------------------
# 2. Main Logic & Routing
# -----------------------------------------------------------------
c_page, c_empty = st.columns([1.5, 2.5])
with c_page:
    page = st.selectbox("Select Board", ["Worldwide KOL Status", "Performance Board"])

st.markdown(
    f"""
    <div class="app-header" style="display:flex; align-items:center;">
        <div>
            <div class="app-title">MEDIT KOL Performance Cockpit : {page}</div>
            <div class="app-subtitle">Global KOL Management System</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# -----------------------------------------------------------------
# 3. Page Content
# -----------------------------------------------------------------

# [Page 1] Worldwide KOL Status
if page == "Worldwide KOL Status":
    total_kol_cnt = df_master["Name"].nunique()
    
    def count_area(keyword_list):
        if "Area" not in df_master.columns: return 0
        mask = df_master["Area"].astype(str).str.lower().apply(lambda x: any(k in x for k in keyword_list))
        return df_master[mask]["Name"].nunique()

    usa_cnt = count_area(["usa", "united states", "north america", "america"])
    europe_cnt = count_area(["europe", "eu"])
    latam_cnt = count_area(["latam", "latin", "south america", "brazil"])

    k1, k2, k3, k4 = st.columns(4)
    with k1: kpi_text("Total KOLs", f"{total_kol_cnt}")
    with k2: kpi_text("USA / NA", f"{usa_cnt}", color=COLOR_NAVY)
    with k3: kpi_text("Europe", f"{europe_cnt}", color=COLOR_NAVY)
    with k4: kpi_text("LATAM", f"{latam_cnt}", color=COLOR_NAVY)

    st.markdown('<div style="height: 30px;"></div>', unsafe_allow_html=True)

    st.markdown("#### KOL Location Map")
    map_html = render_google_map(df_master, area_filter="All")
    components.html(map_html, height=500)
    
    st.markdown('<div style="height: 40px;"></div>', unsafe_allow_html=True)
    
    st.markdown("#### KOL Information")
    
    cols_to_show = [
        "Name",
        "Area",
        "Country",
        "Contract_Start",
        "Contract_End",
        "Delivered_Scanner",
        "Serial_No",
        "PDF_Link",
        "Notion_Link",
    ]
    df_display = df_master[cols_to_show].copy().sort_values("Name")

    def _clean_link(val):
        if isinstance(val, str) and val.startswith("http"):
            return val
        return None

    df_display["PDF_Link"] = df_display["PDF_Link"].apply(_clean_link)
    df_display["Notion_Link"] = df_display["Notion_Link"].apply(_clean_link)
    # 날짜 하이라이트를 위한 기준일 설정
    today = pd.Timestamp.now().normalize()
    soon_threshold = today + pd.Timedelta(days=30)

    def highlight_contract_rows(row):
        ce = row.get("Contract_End")
        if pd.isna(ce):
            return [""] * len(row)
        if ce < today:
            color = "background-color: #FEE2E2"  # red-ish
        elif today <= ce <= soon_threshold:
            color = "background-color: #FEF9C3"  # yellow-ish
        else:
            color = ""
        return [color] * len(row)

    def color_contract_end(val):
        if pd.isna(val):
            return ""
        if val < today:
            return "color: #B91C1C; font-weight: 700;"
        if today <= val <= soon_threshold:
            return "color: #B45309; font-weight: 700;"
        return ""

    def format_date(val):
        if pd.isna(val):
            return ""
        if isinstance(val, (pd.Timestamp, datetime.date)):
            return pd.to_datetime(val).strftime("%Y-%m-%d")
        return str(val)
    
    filter_options = sorted(list(set(
        df_display["Name"].tolist() + 
        df_display["Area"].dropna().unique().tolist() + 
        df_display["Country"].dropna().unique().tolist()
    )))
    
    search_tags = st.multiselect("Filter Data (Name, Area, Country)", options=filter_options, placeholder="Select tags to filter...")
    
    if search_tags:
        mask = df_display.apply(lambda x: any(tag in str(x.values) for tag in search_tags), axis=1)
        df_display = df_display[mask]

    if "selected_kol_ww" not in st.session_state:
        st.session_state["selected_kol_ww"] = "-"

    styled_df = (
        df_display.style
        .apply(highlight_contract_rows, axis=1)
        .applymap(color_contract_end, subset=["Contract_End"])
        .format({"Contract_Start": format_date, "Contract_End": format_date})
    )

    selection = st.dataframe(
        styled_df,
        column_config={
            "Name": st.column_config.TextColumn("Name", width="medium"),
            "Area": st.column_config.TextColumn("Region", width="small"),
            "Country": st.column_config.TextColumn("Country", width="small"),
            "Contract_Start": st.column_config.TextColumn("Contract Start", width="small"),
            "Contract_End": st.column_config.TextColumn("Contract End", width="small"),
            "PDF_Link": st.column_config.LinkColumn("PDF", display_text="Open PDF", width="small"),
            "Notion_Link": st.column_config.LinkColumn("Notion", display_text="Notion Page", width="small"),
        },
        use_container_width=True,
        hide_index=True,
        height=900, 
        on_select="rerun",
        selection_mode="single-row"
    )
    
    if selection and selection["selection"]["rows"]:
        row_idx = selection["selection"]["rows"][0]
        selected_name_from_df = df_display.iloc[row_idx]["Name"]
        if st.session_state["selected_kol_ww"] != selected_name_from_df:
            st.session_state["selected_kol_ww"] = selected_name_from_df
            st.rerun()

    st.markdown("---")
    target_kol = st.session_state["selected_kol_ww"]
    if target_kol and target_kol != "-":
        render_kol_info_box(target_kol, df_master, df_contract)

# [Page 2] Performance Board
elif page == "Performance Board":
    df_activity["Year"] = df_activity["Date"].dt.year
    df_activity["Month_Num"] = df_activity["Date"].dt.month
    available_years = sorted(df_activity["Year"].dropna().unique().tolist())
    today = datetime.date.today()
    default_year = today.year if today.year in available_years else (max(available_years) if available_years else today.year)
    available_month_names = list(MONTH_NAME_MAP.values())

    c_year, c_month, c_area = st.columns(3)
    
    with c_year:
        selected_year = st.selectbox("Year", options=available_years, index=available_years.index(default_year) if default_year in available_years else 0)

    with c_month:
        month_options = ["All"] + available_month_names
        current_month_str = MONTH_NAME_MAP.get(today.month, "Jan")
        default_ix = month_options.index(current_month_str) if current_month_str in month_options else 0
        selected_month_name = st.selectbox("Month", options=month_options, index=default_ix)

    with c_area:
        area_options = ["All"] + sorted(df_master["Area"].dropna().unique().tolist())
        selected_area = st.selectbox("Area", options=area_options, index=0)
    
    mask = df_activity["Year"] == selected_year
    if selected_month_name != "All":
        mask &= df_activity["Month_Num"] == MONTH_NAME_TO_NUM[selected_month_name]
    if selected_area != "All":
        mask &= df_activity["Area"] == selected_area

    df_filtered = df_activity[mask].copy()

    st.markdown(f"### Performance Overview")
    
    total_kols = df_master["Name"].nunique() if selected_area == "All" else df_master[df_master["Area"] == selected_area]["Name"].nunique()
    planned_tasks = df_filtered.shape[0]
    onprogress = df_filtered[df_filtered["Status_norm"] == "On Progress"].shape[0]
    done = df_filtered[df_filtered["Status_norm"] == "Done"].shape[0]
    delayed = df_filtered[df_filtered["Delayed_flag"] == True].shape[0]
    warning = df_filtered[df_filtered["Warning_flag"] == True].shape[0]

    k1, k2, k3, k4, k5, k6 = st.columns(6)
    with k1: kpi_text("Active KOLs", f"{total_kols}")
    with k2: kpi_text("Total Tasks", f"{planned_tasks}")
    with k3: kpi_text("On Progress", f"{onprogress}")
    with k4: kpi_text("Done", f"{done}")
    with k5: kpi_text("Delayed", f"{delayed}", color=COLOR_DANGER)
    with k6: kpi_text("Warning", f"{warning}", color=COLOR_WARNING)

    st.markdown('<div style="height: 30px;"></div>', unsafe_allow_html=True)

    st.markdown("### Monthly All Tasks")
    
    all_keywords = sorted(list(set(
        df_filtered["Name"].tolist() + 
        df_filtered["Task"].astype(str).unique().tolist() + 
        df_filtered["Status_norm"].unique().tolist()
    )))
    
    task_tags = st.multiselect("Filter Tasks (Name, Task, Status)", options=all_keywords, placeholder="Select tags to filter...")
    
    status_df = df_filtered.copy()
    if task_tags:
         mask_task = status_df.apply(lambda x: any(tag in str(x.values) for tag in task_tags), axis=1)
         status_df = status_df[mask_task]
    
    if not status_df.empty:
        status_df["Warning/Delayed"] = status_df.apply(create_warning_delayed_col, axis=1)
        status_cols = ["Date", "Name", "Task", "Activity", "Status_norm", "Warning/Delayed", "Area"]
        status_disp = status_df[status_cols].rename(columns={"Status_norm": "Status"})
        status_disp["Date"] = status_disp["Date"].dt.strftime("%Y-%m-%d")
        status_disp = status_disp.sort_values(by=["Warning/Delayed", "Date"], ascending=[False, True])
        
        # 데이터 양에 따라 높이를 유동적으로 조절 (최소 280, 최대 900)
        height_val = min(max(len(status_disp) * 35 + 80, 280), 900)
        st.dataframe(status_disp.style.apply(highlight_critical_rows, axis=1), use_container_width=True, hide_index=True, height=height_val)
    else:
        st.info("No tasks found for this period.")

    st.markdown('<div style="height: 30px;"></div>', unsafe_allow_html=True)
    st.markdown("### Schedule")
    
    legend_html = '<div style="display: flex; flex-wrap: wrap; gap: 15px; margin-bottom: 10px; font-size: 0.9rem;">'
    for task_name, color in TASK_COLOR_MAP.items():
        legend_html += f'<div style="display: flex; align-items: center;"><span style="display:inline-block; width:12px; height:12px; background-color:{color}; border-radius:50%; margin-right:6px;"></span>{task_name}</div>'
    legend_html += '</div>'
    st.markdown(legend_html, unsafe_allow_html=True)

    if selected_month_name == "All":
        st.info("Please select a specific month to view the Daily Schedule.")
    else:
        events = []
        for _, row in df_filtered.iterrows():
            delayed_flag = bool(row["Delayed_flag"])
            base_color = TASK_COLOR_MAP.get(str(row["Task"]).strip(), COLOR_PRIMARY)
            
            if delayed_flag:
                color = base_color
                border = base_color
                text_color = "#FFFFFF"
                title = f"🚨 {row['Name']} 🚨"
            else:
                color = base_color
                border = base_color
                text_color = "#FFFFFF" 
                title = f"{row['Name']}" 
            
            events.append({
                "title": title,
                "start": row["Date"].strftime("%Y-%m-%d"),
                "end": row["Date"].strftime("%Y-%m-%d"),
                "allDay": True,
                "backgroundColor": color,
                "borderColor": border,
                "textColor": text_color,
                "extendedProps": {"kol_name": row["Name"], "task": row["Task"]}
            })
        
        m_num = MONTH_NAME_TO_NUM[selected_month_name]
        init_date = f"{selected_year}-{m_num:02d}-01"

        cal_state = st_calendar(
            events=events,
            options={
                "initialDate": init_date,
                "headerToolbar": {"left": "", "center": "title", "right": ""},
                "height": 700,
            },
            key=f"cal_{selected_year}_{selected_month_name}"
        )

        if cal_state and cal_state.get("eventClick"):
            clicked_kol = cal_state["eventClick"]["event"]["extendedProps"].get("kol_name")
            if clicked_kol:
                st.markdown("---")
                st.markdown("### KOL Information")
                render_kol_info_box(clicked_kol, df_master, df_contract)
