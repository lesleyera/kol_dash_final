# data.py
import streamlit as st
import pandas as pd
import numpy as np
from streamlit_gsheets import GSheetsConnection
from google.oauth2 import service_account
from googleapiclient.discovery import build

from utils import find_col, normalize_status, delayed_to_bool, warning_to_bool

@st.cache_data(ttl=0)
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
            fields="files(id, name, webViewLink)",
            pageSize=200 
        ).execute()
        
        files = results.get('files', [])
        pdf_map = {}
        
        for f in files:
            name = f['name']
            link = f['webViewLink']
            if name.lower().endswith(".pdf"):
                clean_name = name[:-4].strip() 
            else:
                clean_name = name.strip()
            pdf_map[clean_name] = link
            
        return pdf_map

    except Exception as e:
        return {}

@st.cache_data(ttl=0)
def get_photo_links_from_drive():
    """
    Google Drive 폴더(KOL_Photos)의 파일명을 KOL 이름으로 매핑하여 사진 링크를 반환.
    기본적으로 drive_settings.photo_folder_id를 사용하고, 없으면 제공된 공유 폴더 ID를 fallback으로 사용.
    """
    try:
        gcp_info = st.secrets["gcp_service_account"]
        folder_id = st.secrets["drive_settings"].get("photo_folder_id", "1IDR_brsAc_AGU3yuJhjs2-Sf0MdBVXiR")

        creds = service_account.Credentials.from_service_account_info(
            gcp_info, scopes=['https://www.googleapis.com/auth/drive.readonly']
        )
        service = build('drive', 'v3', credentials=creds)

        results = service.files().list(
            q=f"'{folder_id}' in parents and trashed=false",
            fields="files(id, name, webViewLink, thumbnailLink)",
            pageSize=500
        ).execute()

        files = results.get('files', [])
        photo_map = {}

        for f in files:
            name = f.get('name', '')
            link = f.get('webViewLink')
            thumb = f.get('thumbnailLink')
            # 확장자 제거 후 이름 매핑
            clean_name = name.rsplit(".", 1)[0].strip()
            # 썸네일이 있으면 우선 사용, 없으면 webViewLink 사용
            photo_map[clean_name] = thumb or link

        return photo_map
    except Exception:
        return {}

@st.cache_data(ttl=0)
def load_data(master_tab, contract_tab, activity_tab):
    conn = st.connection("gsheets", type=GSheetsConnection)
    try:
        df_master_raw = conn.read(worksheet=master_tab)
        df_contract = conn.read(worksheet=contract_tab)
        df_act = conn.read(worksheet=activity_tab)
        df_act = df_act.drop_duplicates()
        photo_link_map = get_photo_links_from_drive()

        col_id_m = find_col(df_master_raw, ["KOL_ID", "ID", "No"]) 
        col_name_m = find_col(df_master_raw, ["Name"])
        col_area_m = find_col(df_master_raw, ["Area"])
        col_country_m = find_col(df_master_raw, ["Country"])
        col_notion_m = find_col(df_master_raw, ["Notion", "Link", "Notion Link", "Notion_Link"])
        col_pdf_m = find_col(df_master_raw, ["PDF_Link", "Google_Sheet_Link", "PDF", "Sheet", "Drive", "File"]) 
        col_scanner_m = find_col(df_master_raw, ["Delivered Scanner", "Scanner", "Device"])
        col_serial_m = find_col(df_master_raw, ["Serial No", "Serial", "SN"])
        col_lat_m = find_col(df_master_raw, ["lat", "latitude", "Latitude"])
        col_lon_m = find_col(df_master_raw, ["lon", "longitude", "Longitude"])
        col_hospital_m = find_col(df_master_raw, ["Hospital", "Affiliation"])
        # [Added] Photo Column Detection
        col_photo_m = find_col(df_master_raw, ["Photo", "Image", "Picture", "Profile"])
        
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
        if col_photo_m: rename_m[col_photo_m] = "Photo"
        
        df_master = df_master_raw.rename(columns=rename_m)
        
        # Ensure columns exist
        for col in ["KOL_ID", "Notion_Link", "PDF_Link", "Delivered_Scanner", "Serial_No", "Latitude", "Longitude", "Hospital", "Photo"]:
            if col not in df_master.columns: df_master[col] = "-"

        if "KOL_ID" in df_master.columns:
             df_master["KOL_ID"] = pd.to_numeric(df_master["KOL_ID"], errors='coerce').fillna(0).astype(int)

        drive_pdf_map = get_pdf_links_from_drive()
        
        if "Name" in df_master.columns:
            df_master["Auto_PDF_Link"] = df_master["Name"].astype(str).str.strip().map(drive_pdf_map)
            df_master["Auto_Photo_Link"] = df_master["Name"].astype(str).str.strip().map(photo_link_map)
        else:
            df_master["Auto_PDF_Link"] = None
            df_master["Auto_Photo_Link"] = None
            
        if "PDF_Link" not in df_master.columns:
             df_master["PDF_Link"] = df_master["Auto_PDF_Link"]
        else:
             df_master["PDF_Link"] = df_master["PDF_Link"].replace("-", np.nan).replace("", np.nan)
             df_master["PDF_Link"] = df_master["PDF_Link"].combine_first(df_master["Auto_PDF_Link"])
             df_master["PDF_Link"] = df_master["PDF_Link"].where(pd.notnull(df_master["PDF_Link"]), None)

        # Photo 컬럼 정리: 수동 입력 우선, 없으면 드라이브 자동 매핑
        if "Photo" not in df_master.columns:
             df_master["Photo"] = df_master["Auto_Photo_Link"]
        else:
             df_master["Photo"] = df_master["Photo"].replace("-", np.nan).replace("", np.nan)
             df_master["Photo"] = df_master["Photo"].combine_first(df_master["Auto_Photo_Link"])
             df_master["Photo"] = df_master["Photo"].where(pd.notnull(df_master["Photo"]), None)

        col_name_c = find_col(df_contract, ["Name"])
        col_cstart = find_col(df_contract, ["Contract_Start"])
        col_cend = find_col(df_contract, ["Contract_End"])
        col_times = find_col(df_contract, ["Times", "Time", "Contract Type"])
        df_contract = df_contract.rename(columns={col_name_c: "Name", col_cstart: "Contract_Start", col_cend: "Contract_End", col_times: "Times"})
        if "Times" not in df_contract.columns: df_contract["Times"] = "-"
        if "Contract_Start" not in df_contract.columns: df_contract["Contract_Start"] = pd.NaT
        if "Contract_End" not in df_contract.columns: df_contract["Contract_End"] = pd.NaT
        
        df_contract["Contract_Start"] = pd.to_datetime(df_contract["Contract_Start"], errors="coerce")
        df_contract["Contract_End"] = pd.to_datetime(df_contract["Contract_End"], errors="coerce")

        if "Contract_End" in df_contract.columns and "Name" in df_contract.columns:
            latest_contracts = (
                df_contract
                .sort_values("Contract_End")
                .groupby("Name")
                .tail(1)[["Name", "Contract_Start", "Contract_End"]]
            )
            df_master = df_master.merge(latest_contracts, on="Name", how="left")
        else:
            df_master["Contract_Start"] = pd.NaT
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
