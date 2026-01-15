# auth.py
import streamlit as st
import time
from config import ACCESS_CODE, COLOR_PRIMARY

def check_password():
    """로그인 화면"""
    
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
            .login-container {{ background-color: transparent; padding: 60px 20px; text-align: center; max-width: 600px; margin: 8vh auto 0 auto; }}
            .login-title {{ font-size: 2.8rem; font-weight: 900; color: {COLOR_PRIMARY}; margin-bottom: 40px; white-space: nowrap; letter-spacing: -0.5px; line-height: 1.2; text-align: center; }}
            .input-label {{ font-size: 1rem; font-weight: 700; color: #555; margin-bottom: 15px; text-transform: uppercase; letter-spacing: 1.2px; display: block; text-align: center; }}
            .stTextInput {{ width: 100%; max-width: 400px; margin-left: auto !important; margin-right: auto !important; }}
            .stTextInput > div > div > input {{ padding: 16px 20px; font-size: 1.2rem; border: 1px solid #D1D5DB !important; border-radius: 12px; text-align: center; background-color: #FAFAFA; color: #333; box-shadow: none !important; transition: all 0.2s ease; }}
            .stTextInput > div > div > input:focus {{ border-color: {COLOR_PRIMARY} !important; background-color: #fff; box-shadow: 0 0 0 3px rgba(43, 92, 215, 0.15) !important; }}
            div[data-testid="stButton"] {{ width: 100% !important; display: flex; justify-content: center; margin-top: 20px; }}
            div[data-testid="stButton"] > button {{ background-color: {COLOR_PRIMARY}; color: white; border: none; padding: 14px 60px; font-size: 1.1rem; border-radius: 50px; cursor: pointer; font-weight: 700; transition: background-color 0.2s, transform 0.1s; box-shadow: 0 4px 12px rgba(0, 32, 96, 0.2); }}
            div[data-testid="stButton"] > button:hover {{ background-color: #1e4bb8; color: white; border: none; }}
            .error-msg {{ color: #D32F2F; background-color: #FEF2F2; padding: 12px; border-radius: 8px; font-size: 0.9rem; margin-top: 30px; font-weight: 600; text-align: center; }}
            .login-footer {{ margin-top: 100px; font-size: 0.8rem; color: #CBD5E0; font-weight: 400; text-align: center; width: 100%; display: block; }}
            header {{visibility: hidden;}} footer {{visibility: hidden;}}
            </style>
            """, unsafe_allow_html=True
        )
        col1, col2, col3 = st.columns([1, 1.5, 1])
        with col2:
            st.markdown('<div class="login-container">', unsafe_allow_html=True)
            col_img1, col_img2, col_img3 = st.columns([1, 1, 1])
            with col_img2:
                try: st.image("image_0.png", width=60)
                except: pass
            st.markdown('<div class="login-title">MEDIT KOL Performance Cockpit</div>', unsafe_allow_html=True)
            inner_left, inner_center, inner_right = st.columns([1, 2, 1])
            with inner_center:
                st.markdown('<div class="input-label">Access Code</div>', unsafe_allow_html=True)
                st.text_input("Password", type="password", key="password", on_change=password_entered, label_visibility="collapsed")
                st.button("Enter", on_click=password_entered, use_container_width=True)
            if st.session_state.get("auth_error"):
                st.markdown('<div class="error-msg">⚠️ Incorrect Access Code</div>', unsafe_allow_html=True)
            st.markdown('<div class="login-footer">© 2025 powered by DWG Inc.</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        return False
    return True