# utils.py
import streamlit as st
import pandas as pd
from config import COLOR_BG, COLOR_PRIMARY, COLOR_NAVY

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