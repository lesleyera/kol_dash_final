import streamlit as st
import pandas as pd
import numpy as np
import datetime
import os
import time
import re
import streamlit.components.v1 as components
from streamlit_calendar import calendar as st_calendar
from PIL import Image

# [추가] 구글 연동 라이브러리
from streamlit_gsheets import GSheetsConnection
from google.oauth2 import service_account
from googleapiclient.discovery import build

import folium
from streamlit_folium import st_folium

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

# [설정] 색상 정의
ACCESS_CODE = "medit2026"
COLOR_PRIMARY = "#2B5CD7"  # [Main] Royal Blue
COLOR_NAVY = "#002060"     # [Sub] Navy Blue
COLOR_DANGER = "#DC2626"   # Red
COLOR_WARNING = "#F59E0B"  # Orange
COLOR_BG = "#FFFFFF"       # White

# [설정] 구글 맵 API 키
GOOGLE_MAPS_API_KEY = "AIzaSyBboTIDL47Dt0ayBAgSRk-SixRphzfhKSg"

# 세션 상태 초기화
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

# -----------------------------------------------------------------
# 로그인 & 세션 관리
# -----------------------------------------------------------------
def check_password():
    """로그인 화면 (버튼 수직 정렬 완벽 수정)"""
    
    # 세션 관리
    if "last_active" in st.session_state:
        if time.time() - st.session_state["last_active"] > 1200:
            st.session_state["authenticated"] = False
            st.query_params.clear()
            del st.session_state["last_active"]
            st.rerun()
        else:
            st.session_state["last_active"] = time.time()

    if not st.session_state.get("authenticated", False):
        if st.query_params.get("logged_in") == "true":
            st.session_state["authenticated"] = True
            st.session_state["last_active"] = time.time()

    def password_entered():
        entered = st.session_state.get("password", "")
        if entered == ACCESS_CODE:
            st.session_state["authenticated"] = True
            st.session_state["last_active"] = time.time()
            st.query_params["logged_in"] = "true"
            st.session_state["auth_error"] = False
        else:
            st.session_state["authenticated"] = False
            st.session_state["auth_error"] = True

    if not st.session_state.get("authenticated", False):
        st.markdown(
            f"""
            <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800;900&display=swap');
            
            .stApp {{ background-color: #FFFFFF; font-family: 'Inter', sans-serif; }}
            
            /* 로그인 컨테이너 (투명) */
            .login-container {{
                background-color: transparent;
                padding: 60px 20px;
                text-align: center;
                max-width: 600px; 
                margin: 8vh auto 0 auto; 
            }}

            /* 🔹 입력 + 버튼 세트 래퍼 (가운데 정렬용) */
            .login-inner {{
                max-width: 400px;
                margin: 0 auto;
            }}
            
            /* 타이틀 */
            .login-title {{
                font-size: 2.8rem; font-weight: 900; 
                color: {COLOR_PRIMARY};
                margin-bottom: 40px; white-space: nowrap; 
                letter-spacing: -0.5px; line-height: 1.2; text-align: center;
            }}
            
            /* 라벨 */
            .input-label {{
                font-size: 1rem; font-weight: 700; color: #555; 
                margin-bottom: 15px; text-transform: uppercase; 
                letter-spacing: 1.2px; display: block; text-align: center;
            }}
            
            /* 입력창 컴포넌트 중앙 정렬 */
            .stTextInput {{ 
                width: 100%; 
                max-width: 400px; 
                margin-left: auto !important; 
                margin-right: auto !important; 
            }}
            
            .stTextInput > div > div > input {{
                padding: 16px 20px; font-size: 1.2rem; 
                border: 1px solid #D1D5DB !important;
                border-radius: 12px; text-align: center; 
                background-color: #FAFAFA; color: #333;
                box-shadow: none !important; transition: all 0.2s ease;
            }}
            .stTextInput > div > div > input:focus {{
                border-color: {COLOR_PRIMARY} !important; background-color: #fff;
                box-shadow: 0 0 0 3px rgba(43, 92, 215, 0.15) !important;
            }}
            
            /* 버튼 컴포넌트 중앙 정렬 */
            div[data-testid="stButton"] {{
                width: 100% !important;
                display: flex;
                justify-content: center;
                margin-top: 20px;
            }}
            
            div[data-testid="stButton"] > button {{
                background-color: {COLOR_PRIMARY}; color: white; 
                border: none; padding: 14px 60px;
                font-size: 1.1rem; border-radius: 50px; 
                cursor: pointer; font-weight: 700;
                transition: background-color 0.2s, transform 0.1s; 
                box-shadow: 0 4px 12px rgba(0, 32, 96, 0.2);
            }}
            div[data-testid="stButton"] > button:hover {{ 
                background-color: #1e4bb8; color: white; border: none;
            }}
            
            .error-msg {{
                color: #D32F2F; background-color: #FEF2F2; 
                padding: 12px; border-radius: 8px; font-size: 0.9rem; 
                margin-top: 30px; font-weight: 600; text-align: center;
            }}
            
            .login-footer {{ 
                margin-top: 100px; font-size: 0.8rem; 
                color: #CBD5E0; font-weight: 400; text-align: center; 
                width: 100%; display: block;
            }}
            
            header {{visibility: hidden;}} footer {{visibility: hidden;}}
            </style>
            """, unsafe_allow_html=True
        )
        
        # 3-컬럼 레이아웃 그대로 유지
        col1, col2, col3 = st.columns([1, 1.5, 1])
        
        with col2:
            st.markdown('<div class="login-container">', unsafe_allow_html=True)
            
            # 로고 이미지 중앙 정렬
            col_img1, col_img2, col_img3 = st.columns([1, 1, 1])
            with col_img2:
                try:
                    st.image("image_0.png", width=60)
                except:
                    pass
            
            st.markdown('<div class="login-title">MEDIT KOL Performance Cockpit</div>', unsafe_allow_html=True)
            
             # 🔹 Access Code + Enter 버튼을 같은 세로축 중앙에 배치
            inner_left, inner_center, inner_right = st.columns([1, 2, 1])
            with inner_center:
                st.markdown('<div class="input-label">Access Code</div>', unsafe_allow_html=True)

                st.text_input(
                    "Password",
                    type="password",
                    key="password",
                    on_change=password_entered,
                    label_visibility="collapsed"
                )

                # 버튼 (입력창과 같은 중앙축, 바로 아래 위치)
                st.button("Enter", on_click=password_entered, use_container_width=True)

            if st.session_state.get("auth_error"):
                st.markdown(
                    '<div class="error-msg">⚠️ Incorrect Access Code</div>',
                    unsafe_allow_html=True
                )
            
            st.markdown('<div class="login-footer">© 2025 powered by DWG Inc.</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)  # </div class="login-container">

        return False
    
    return True


if not check_password():
    st.stop()


# -----------------------------------------------------------------
# 1. CSS Styles (Main Dashboard)
# -----------------------------------------------------------------
def local_css():
    st.markdown(
        f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800;900&display=swap');
        
        html, body, [class*="css"] {{ font-family: 'Inter', sans-serif !important; }}
        .stApp {{ background-color: {COLOR_BG}; color: #111; font-family: 'Inter', sans-serif !important; }}
        .block-container {{ padding-top: 6rem !important; padding-bottom: 4rem !important; }}

        /* Header Box */
        .app-header {{
            background: linear-gradient(135deg, {COLOR_PRIMARY} 0%, #1e4bb8 100%);
            border-radius: 12px; padding: 24px 32px;
            box-shadow: 0 4px 20px rgba(43, 92, 215, 0.2);
            color: #FFFFFF; margin-bottom: 30px; margin-top: 10px; 
        }}
        .app-title {{
            font-size: 1.8rem; font-weight: 800; color: #FFFFFF !important;
            margin-bottom: 4px; font-family: 'Inter', sans-serif !important;
        }}
        .app-subtitle {{ font-size: 0.95rem; opacity: 0.9; font-weight: 300; }}
        
        /* Table Headers */
        thead tr th {{
            background-color: {COLOR_PRIMARY} !important; color: #FFFFFF !important; 
            font-size: 13px !important; font-weight: 600 !important;
            text-transform: uppercase; font-family: 'Inter', sans-serif !important;
        }}

        /* Info Box */
        .info-box {{
            background-color: #FFFFFF; padding: 24px; border-radius: 12px;
            border: 1px solid #E5E7EB; box-shadow: 0 2px 8px rgba(0,0,0,0.03); margin-bottom: 20px;
        }}
        .profile-label {{ font-size: 0.85rem; color: #6B7280; font-weight: 600; margin-bottom: 5px; text-transform: uppercase; }}
        .profile-value {{ font-size: 1.1rem; color: #111; font-weight: 700; }}
        .info-label {{ font-size: 0.8rem; color: #6B7280; text-transform: uppercase; font-weight: 700; margin-bottom: 4px; }}
        .info-val {{ font-size: 1.1rem; font-weight: 600; color: #111827; margin-bottom: 16px; }}

        /* 중제목(Sub-headers) */
        .section-title, h3, h4 {{
            font-size: 1.6rem !important; font-weight: 800 !important;
            color: {COLOR_NAVY} !important;
            margin-bottom: 20px; margin-top: 30px;
            font-family: 'Inter', sans-serif !important;
        }}

        /* Buttons */
        .box-btn {{
            display: inline-flex; align-items: center; justify-content: center;
            padding: 8px 16px; font-size: 0.9rem; font-weight: 600;
            color: {COLOR_PRIMARY}; background-color: #EFF6FF; border: 1px solid {COLOR_PRIMARY};
            border-radius: 6px; text-decoration: none; margin-right: 10px; transition: all 0.2s;
            min-width: 140px;
        }}
        .box-btn:hover {{ background-color: {COLOR_PRIMARY}; color: #FFFFFF; text-decoration: none; }}
        
        /* Status Headers */
        .status-section-header {{
            font-size: 1.2rem; font-weight: 700; color: #333;
            margin-top: 30px; margin-bottom: 12px; display: flex; align-items: center;
        }}
        .status-indicator {{
            width: 12px; height: 12px; border-radius: 50%; margin-right: 10px;
        }}
    </style>
    """, unsafe_allow_html=True)
local_css()

# -----------------------------------------------------------------
# 2. Data & Helper Functions
# -----------------------------------------------------------------
# [수정] 탭 이름만 설정 (URL 및 파일 경로는 secrets 사용)
FILE_SETTINGS = {
    "MASTER_TAB": "kol_master",
    "CONTRACT_TAB": "contract_tasks",
    "ACTIVITY_TAB": "activity_log",
}

MONTH_NAME_MAP = {1:"Jan",2:"Feb",3:"Mar",4:"Apr",5:"May",6:"Jun",7:"Jul",8:"Aug",9:"Sep",10:"Oct",11:"Nov",12:"Dec"}
MONTH_NAME_TO_NUM = {v: k for k, v in MONTH_NAME_MAP.items()}
TASK_COLOR_MAP = {"Lecture":"#1D4ED8","Case Report":"#0EA5E9","SNS Posting":"#EC4899","Article":"#F97316","Webinar":"#22C55E","Testimonial":"#6366F1"}
STATUS_COLORS = {"TBD": "#9CA3AF", "Planned": "#3B82F6", "On Progress": "#F59E0B", "Done": "#10B981"}

def find_col(df, candidates):
    cols = list(df.columns)
    norm = {c: c.strip().lower().replace(" ", "_").replace("(", "").replace(")", "").replace("/", "_") for c in cols}
    normalized_candidates = [c.strip().lower().replace(" ", "_").replace("(", "").replace(")", "").replace("/", "_") for c in candidates]
    for original, n in norm.items():
        for nc in normalized_candidates:
            if nc in n: return original
    return None

def normalize_status(val: str) -> str:
    if pd.isna(val): return "Planned"
    s = str(val).strip().lower().replace("_", " ").replace("-", " ")
    if s in ["planned", "plan"]: return "Planned"
    if any(x in s for x in ["on progress", "in progress", "ongoing", "doing"]): return "On Progress"
    if any(x in s for x in ["done", "finished", "complete", "completed", "end"]): return "Done"
    if any(x in s for x in ["tbd", "to be determined"]): return "TBD"
    return s.title()

def delayed_to_bool(val) -> bool:
    if pd.isna(val): return False
    s = str(val).strip().lower()
    return s in ["1", "y", "yes", "true", "delayed", "delay", "o"]

def warning_to_bool(val) -> bool:
    if pd.isna(val): return False
    s = str(val).strip().lower()
    return "warning" in s

def highlight_critical_rows(row):
    style = ''
    status_val = ""
    if "Delayed" in row.index: status_val = str(row["Delayed"]).lower()
    elif "Warning/Delayed" in row.index: status_val = str(row["Warning/Delayed"]).lower()
    if "delayed" in status_val: style = 'background-color: #FEE2E2; color: #991B1B; font-weight: bold;'
    elif "warning" in status_val: style = 'background-color: #FEF3C7; color: #92400E; font-weight: bold;'
    return [style] * len(row)

def create_warning_delayed_col(row):
    if row.get("Delayed_flag") is True: return "Delayed"
    elif row.get("Warning_flag") is True: return "Warning"
    return "-"

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
        df_map["Longitude"] = df_map["Latitude_Raw"]
        df_map["Latitude"] = df_map["Longitude_Raw"]
        map_center_lat = df_map["Longitude"].mean()
        map_center_lng = df_map["Latitude"].mean()

        markers_list = []
        for _, row in df_map.iterrows():
            name = row.get("Name", "Unknown")
            info_content = f"<b>{name}</b><br>{row.get('Hospital','')}"
            markers_list.append({"name": name, "lat": float(row["Longitude"]), "lng": float(row["Latitude"]), "info": info_content})
        import json as _json
        markers_json = _json.dumps(markers_list)

    html_code = f"""
    <!DOCTYPE html><html><head><style>#map {{ height: 100%; width: 100%; border-radius: 12px; }} html, body {{ height: 100%; margin: 0; padding: 0; }}</style></head>
    <body><div id="map"></div><script>
    function initMap() {{
        const map = new google.maps.Map(document.getElementById("map"), {{ zoom: {3 if area_filter == 'All' else 4}, center: {{ lat: {map_center_lat}, lng: {map_center_lng} }}, mapTypeControl: false, streetViewControl: false }});
        const markersData = {markers_json};
        const infoWindow = new google.maps.InfoWindow();
        markersData.forEach((data) => {{
            const marker = new google.maps.Marker({{ position: {{ lat: data.lat, lng: data.lng }}, map: map, title: data.name }});
            marker.addListener("click", () => {{ infoWindow.setContent(data.info); infoWindow.open(map, marker); }});
        }});
    }}</script><script src="https://maps.googleapis.com/maps/api/js?key={api_key}&callback=initMap" async defer></script></body></html>
    """
    return html_code

# -----------------------------------------------------------------
# [추가] 구글 드라이브 PDF 링크 자동 수집 함수
# -----------------------------------------------------------------
@st.cache_data(ttl=600)
def get_pdf_links_from_drive():
    try:
        gcp_info = st.secrets["gcp_service_account"]
        folder_id = st.secrets["drive_settings"]["folder_id"]

        creds = service_account.Credentials.from_service_account_info(
            gcp_info, scopes=['https://www.googleapis.com/auth/drive.readonly']
        )
        service = build('drive', 'v3', credentials=creds)

        results = service.files().list(
            q=f"'{folder_id}' in parents and trashed=false",
            fields="nextPageToken, files(id, name, webViewLink)",
            pageSize=1000
        ).execute()
        
        files = results.get('files', [])
        pdf_map = {}
        for f in files:
            name = f['name']
            link = f['webViewLink']
            match = re.match(r"^(\d+)", name)
            if match:
                kol_id = match.group(1)
                pdf_map[kol_id] = link
        return pdf_map

    except Exception as e:
        # 오류 발생 시 빈 dict 반환 (로컬 테스트나 설정 미비 시 앱이 죽지 않도록)
        # st.warning(f"Drive API Error: {e}") 
        return {}

# -----------------------------------------------------------------
# [수정] 데이터 로드 (구글 시트 + 드라이브 연동)
# -----------------------------------------------------------------
@st.cache_data(ttl=600)
def load_data(master_tab, contract_tab, activity_tab):
    conn = st.connection("gsheets", type=GSheetsConnection)
    try:
        df_master_raw = conn.read(worksheet=master_tab)
        df_contract = conn.read(worksheet=contract_tab)
        df_act = conn.read(worksheet=activity_tab)
        df_act = df_act.drop_duplicates()

        col_id_m = find_col(df_master_raw, ["KOL_ID", "ID", "No"]) 
        col_name_m = find_col(df_master_raw, ["Name"])
        col_area_m = find_col(df_master_raw, ["Area"])
        col_country_m = find_col(df_master_raw, ["Country"])
        
        # [수정] Notion, PDF 컬럼 매칭 (컬럼명이 다양할 수 있어 여러 후보군 지정)
        col_notion_m = find_col(df_master_raw, ["Notion", "Link", "Notion Link", "Notion_Link"])
        col_pdf_m = find_col(df_master_raw, ["PDF_Link", "Google_Sheet_Link", "PDF", "Sheet", "Drive", "File"]) 
        
        col_scanner_m = find_col(df_master_raw, ["Delivered Scanner", "Scanner", "Device"])
        col_serial_m = find_col(df_master_raw, ["Serial No", "Serial", "SN"])
        col_lat_m = find_col(df_master_raw, ["lat", "latitude", "Latitude"])
        col_lon_m = find_col(df_master_raw, ["lon", "longitude", "Longitude"])
        col_hospital_m = find_col(df_master_raw, ["Hospital", "Affiliation"])
        
        rename_m = {
            col_name_m: "Name", 
            col_area_m: "Area", 
            col_country_m: "Country", 
        }
        if col_id_m: rename_m[col_id_m] = "KOL_ID"
        if col_notion_m: rename_m[col_notion_m] = "Notion_Link"
        if col_pdf_m: rename_m[col_pdf_m] = "PDF_Link"
        if col_scanner_m: rename_m[col_scanner_m] = "Delivered_Scanner"
        if col_serial_m: rename_m[col_serial_m] = "Serial_No"
        if col_lat_m: rename_m[col_lat_m] = "Latitude"
        if col_lon_m: rename_m[col_lon_m] = "Longitude"
        if col_hospital_m: rename_m[col_hospital_m] = "Hospital"
        
        df_master = df_master_raw.rename(columns=rename_m)
        
        # 누락된 컬럼 처리
        for col in ["KOL_ID", "Notion_Link", "PDF_Link", "Delivered_Scanner", "Serial_No", "Latitude", "Longitude", "Hospital"]:
            if col not in df_master.columns: df_master[col] = "-"

        # [수정] KOL_ID를 Int형으로 변환
        if "KOL_ID" in df_master.columns:
             # 숫자로 변환 (실패 시 NaN), NaN은 0으로 채우고 정수로 변환
             df_master["KOL_ID"] = pd.to_numeric(df_master["KOL_ID"], errors='coerce').fillna(0).astype(int)

        # [추가] 구글 드라이브 PDF 자동 연동
        # 시트에 PDF 링크가 없어도 드라이브에서 KOL_ID로 찾아 채워넣음
        drive_pdf_map = get_pdf_links_from_drive()
        
        if "KOL_ID" in df_master.columns:
            # KOL_ID를 문자열로 정리
            df_master["KOL_ID_Str"] = df_master["KOL_ID"].astype(str).str.replace(".0", "").str.strip()
            df_master["Auto_PDF_Link"] = df_master["KOL_ID_Str"].map(drive_pdf_map)
        else:
            df_master["Auto_PDF_Link"] = None
            
        # PDF_Link 우선순위: 수동입력 > 자동매칭
        if "PDF_Link" not in df_master.columns:
             df_master["PDF_Link"] = df_master["Auto_PDF_Link"]
        else:
             # 빈 값이나 '-'인 경우 자동 링크로 대체
             df_master["PDF_Link"] = df_master["PDF_Link"].replace("-", np.nan).replace("", np.nan)
             df_master["PDF_Link"] = df_master["PDF_Link"].combine_first(df_master["Auto_PDF_Link"])
             df_master["PDF_Link"] = df_master["PDF_Link"].fillna("-")

        col_name_c = find_col(df_contract, ["Name"])
        col_cstart = find_col(df_contract, ["Contract_Start"])
        col_cend = find_col(df_contract, ["Contract_End"])
        col_times = find_col(df_contract, ["Times", "Time", "Contract Type"])
        df_contract = df_contract.rename(columns={col_name_c: "Name", col_cstart: "Contract_Start", col_cend: "Contract_End", col_times: "Times"})
        df_contract["Contract_Start"] = pd.to_datetime(df_contract["Contract_Start"], errors="coerce")
        df_contract["Contract_End"] = pd.to_datetime(df_contract["Contract_End"], errors="coerce")
        if "Times" not in df_contract.columns: df_contract["Times"] = "-"

        if "Contract_End" in df_contract.columns and "Name" in df_contract.columns:
            latest_contracts = df_contract.sort_values("Contract_End").groupby("Name").tail(1)[["Name", "Contract_End"]]
            df_master = df_master.merge(latest_contracts, on="Name", how="left")
        else:
            df_master["Contract_End"] = pd.NaT

        col_name_a = find_col(df_act, ["Name"])
        col_date = find_col(df_act, ["Date"])
        col_task_a = find_col(df_act, ["Task"])
        col_activity_a = find_col(df_act, ["Activity", "Details"])
        col_status = find_col(df_act, ["Status"])
        col_delayed = find_col(df_act, ["Delayed"])
        col_source = find_col(df_act, ["Source", "Evidence"])
        
        df_act = df_act.rename(columns={col_name_a: "Name", col_date: "Date", col_task_a: "Task", col_activity_a: "Activity", col_status: "Status", col_delayed: "Delayed"})
        if col_source: df_act = df_act.rename(columns={col_source: "Source"})
        else: df_act["Source"] = ""

        df_act["Date"] = pd.to_datetime(df_act["Date"], errors="coerce")
        df_act = df_act.dropna(subset=["Date"])
        df_act["Status_norm"] = df_act["Status"].apply(normalize_status)
        df_act["Delayed_flag"] = df_act["Delayed"].apply(delayed_to_bool)
        df_act["Warning_flag"] = df_act["Delayed"].apply(warning_to_bool)
        df_act = df_act.merge(df_master[["Name", "Area", "Country"]].drop_duplicates("Name"), on="Name", how="left")
        
        return df_master, df_contract, df_act
    except Exception as e:
        st.error(f"Data Load Error: {e}")
        return None, None, None

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
    
    # [수정] 링크 유효성 체크 및 버튼 렌더링
    notion_url = info.iloc[0]["Notion_Link"] if not info.empty else None
    pdf_url = info.iloc[0]["PDF_Link"] if not info.empty else None 

    # PDF 버튼
    if pdf_url and str(pdf_url).startswith("http"):
        pdf_btn_html = f'<a href="{pdf_url}" target="_blank" class="box-btn">📂 Open PDF (Drive)</a>'
    else:
        pdf_btn_html = '<span style="color:#ccc; font-size:0.85rem; margin-right:10px;">🚫 No PDF</span>'

    # Notion 버튼
    if notion_url and str(notion_url).startswith("http"):
        notion_btn_html = f'<a href="{notion_url}" target="_blank" class="box-btn">🔗 Notion Page</a>'
    else:
        notion_btn_html = '<span style="color:#ccc; font-size:0.85rem;">🚫 No Notion</span>'

    html_content = f"""
    <div class="info-box">
        <div style="display:flex; justify-content: space-between; flex-wrap: wrap; margin-bottom: 20px;">
            <div style="margin-right:20px;">
                <div class="info-label">Name</div>
                <div class="info-val">{kol_name}</div>
            </div>
            <div style="margin-right:20px;">
                <div class="info-label">Region</div>
                <div class="info-val">{area}</div>
            </div>
            <div style="margin-right:20px;">
                <div class="info-label">Country</div>
                <div class="info-val">{country}</div>
            </div>
            <div style="margin-right:20px;">
                <div class="info-label">Contract Period</div>
                <div class="info-val">{contract_period_str}</div>
            </div>
            <div style="margin-right:20px;">
                <div class="info-label">Contract Type</div>
                <div class="info-val" style="color:{COLOR_PRIMARY}">{contract_times_str}</div>
            </div>
        </div>
        <div style="display:flex; justify-content: flex-start; flex-wrap: wrap; margin-bottom: 20px; border-top: 1px dashed #eee; padding-top: 15px;">
            <div style="margin-right:40px;">
                <div class="info-label">Delivered Scanner</div>
                <div class="info-val">{scanner}</div>
            </div>
            <div style="margin-right:40px;">
                <div class="info-label">Serial No.</div>
                <div class="info-val">{serial_no}</div>
            </div>
        </div>
        <div style="padding-top:15px; border-top:1px solid #eee;">
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
    else:
        st.info("No activity records found.")

# -----------------------------------------------------------------
# 3. Main Logic
# -----------------------------------------------------------------
df_master, df_contract, df_activity = load_data(
    FILE_SETTINGS["MASTER_TAB"], FILE_SETTINGS["CONTRACT_TAB"], FILE_SETTINGS["ACTIVITY_TAB"]
)

if df_master is None: st.stop()

df_activity["Year"] = df_activity["Date"].dt.year
df_activity["Month_Num"] = df_activity["Date"].dt.month
available_years = sorted(df_activity["Year"].dropna().unique().tolist())
today = datetime.date.today()
default_year = today.year if today.year in available_years else (max(available_years) if available_years else today.year)
available_month_names = list(MONTH_NAME_MAP.values())

c_page, c_year, c_month, c_area = st.columns([1.5, 0.8, 0.8, 1.0])

with c_page:
    page = st.selectbox("Select Board", ["Worldwide KOL Status", "Performance Board", "Admin Board"])

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

mask = df_activity["Year"] == selected_year
if selected_month_name != "All":
    mask &= df_activity["Month_Num"] == MONTH_NAME_TO_NUM[selected_month_name]
if selected_area != "All":
    mask &= df_activity["Area"] == selected_area

df_filtered = df_activity[mask].copy()

# -----------------------------------------------------------------
# 5. Worldwide KOL Status
# -----------------------------------------------------------------
if page == "Worldwide KOL Status":
    st.markdown("#### KOL Location Map")
    map_html = render_google_map(df_master, area_filter=selected_area)
    components.html(map_html, height=500)
    
    st.markdown('<div style="height: 30px;"></div>', unsafe_allow_html=True)
    
    st.markdown("#### KOL List")
    
    df_list = df_master.copy()
    if selected_area != "All":
        df_list = df_list[df_list["Area"] == selected_area]
        
    cols_to_show = ["KOL_ID", "Name", "Area", "Country", "Delivered_Scanner", "Serial_No", "PDF_Link", "Notion_Link", "Contract_End"]
    
    if "Contract_End" not in df_list.columns:
        df_list["Contract_End"] = pd.NaT

    df_display = df_list[cols_to_show].copy()
    df_display = df_display.sort_values(by="KOL_ID")

    def highlight_contract_expiring(row):
        styles = [''] * len(row)
        if selected_month_name == "All":
            return styles
        
        c_end = row.get("Contract_End")
        if pd.isna(c_end):
            return styles
            
        target_m = MONTH_NAME_TO_NUM[selected_month_name]
        if c_end.year == selected_year and c_end.month == target_m:
            for i, col in enumerate(row.index):
                if col == "Contract_End":
                    styles[i] = 'background-color: #FECACA; color: #991B1B; font-weight: bold;'
        return styles

    height_val = (len(df_display) + 1) * 35 + 3
    st.dataframe(
        df_display.style.apply(highlight_contract_expiring, axis=1),
        column_config={
            "KOL_ID": st.column_config.TextColumn("KOL ID", width="small"),
            "Name": st.column_config.TextColumn("Name", width="medium"),
            "Area": st.column_config.TextColumn("Region", width="small"),
            "Country": st.column_config.TextColumn("Country", width="small"),
            "Delivered_Scanner": st.column_config.TextColumn("Scanner", width="small"),
            "Serial_No": st.column_config.TextColumn("Serial No.", width="medium"),
            "PDF_Link": st.column_config.LinkColumn("PDF (Drive)", display_text="Open"),
            "Notion_Link": st.column_config.LinkColumn("Notion", display_text="View"),
            "Contract_End": st.column_config.DateColumn("Contract End", format="YYYY-MM-DD", width="medium"),
        },
        use_container_width=True,
        hide_index=True,
        height=height_val
    )

# -----------------------------------------------------------------
# 6. Performance Board
# -----------------------------------------------------------------
elif page == "Performance Board":
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

    st.markdown("### Active & Delayed Tasks")
    status_df = df_filtered[
        (df_filtered["Status_norm"] == "On Progress") | 
        (df_filtered["Delayed_flag"] == True) | 
        (df_filtered["Warning_flag"] == True)
    ].copy()
    
    if not status_df.empty:
        status_df["Warning/Delayed"] = status_df.apply(create_warning_delayed_col, axis=1)
        status_cols = ["Date", "Name", "Task", "Activity", "Status_norm", "Warning/Delayed", "Area"]
        status_disp = status_df[status_cols].rename(columns={"Status_norm": "Status"})
        status_disp["Date"] = status_disp["Date"].dt.strftime("%Y-%m-%d")
        status_disp = status_disp.sort_values(by=["Warning/Delayed", "Date"], ascending=[False, True])
        
        height_val = (len(status_disp) + 1) * 35 + 3
        st.dataframe(status_disp.style.apply(highlight_critical_rows, axis=1), use_container_width=True, hide_index=True, height=height_val)
    else:
        st.info("No active or delayed tasks.")

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

# -----------------------------------------------------------------
# 7. Admin Board
# -----------------------------------------------------------------
else: # Admin Board
    
    st.markdown("### Activity Log Viewer")
    
    df_log = df_filtered.copy()
    df_log["Warning/Delayed"] = df_log.apply(create_warning_delayed_col, axis=1)
    df_log["Date"] = df_log["Date"].dt.strftime("%Y-%m-%d")
    
    cols_admin = ["Date", "Name", "Area", "Country", "Task", "Activity", "Warning/Delayed"]
    
    statuses = ["TBD", "Planned", "On Progress", "Done"]
    
    for status in statuses:
        color = STATUS_COLORS.get(status, "#333")
        st.markdown(
            f"""
            <div class="status-section-header">
                <div class="status-indicator" style="background-color: {color};"></div>
                {status}
            </div>
            """, unsafe_allow_html=True
        )
        
        subset = df_log[df_log["Status_norm"] == status].copy()
        subset = subset.sort_values(by="Date", ascending=True) 
        
        if not subset.empty:
            cols_real = [c for c in cols_admin if c in subset.columns]
            
            height_val = (len(subset) + 1) * 35 + 3
            st.dataframe(
                subset[cols_real].style.apply(highlight_critical_rows, axis=1),
                use_container_width=True, hide_index=True,
                height=height_val
            )
        else:
            st.caption(f"No {status} tasks.")

    st.markdown('<div style="height: 40px;"></div>', unsafe_allow_html=True)
    st.markdown("---")

    st.markdown("### KOL Information")
    
    all_kol_names = sorted(df_master["Name"].dropna().unique().tolist())
    target_kol = st.selectbox("Select KOL to view Details", ["-"] + all_kol_names)
    
    if target_kol != "-":
        render_kol_detail_admin(target_kol, df_master, df_contract, df_activity)