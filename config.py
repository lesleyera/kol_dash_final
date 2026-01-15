# config.py
import datetime

# [설정] 기본 상수
ACCESS_CODE = "medit2026"
COLOR_PRIMARY = "#2B5CD7"  # [Main] Royal Blue
COLOR_NAVY = "#002060"     # [Sub] Navy Blue
COLOR_DANGER = "#DC2626"   # Red
COLOR_WARNING = "#F59E0B"  # Orange
COLOR_BG = "#FFFFFF"       # White

# [설정] 구글 맵 API 키
GOOGLE_MAPS_API_KEY = "AIzaSyBboTIDL47Dt0ayBAgSRk-SixRphzfhKSg"

# [설정] 파일 및 시트 탭 이름
FILE_SETTINGS = {
    "MASTER_TAB": "kol_master",
    "CONTRACT_TAB": "contract_tasks",
    "ACTIVITY_TAB": "activity_log",
}

# [설정] 매핑 정보
MONTH_NAME_MAP = {1:"Jan",2:"Feb",3:"Mar",4:"Apr",5:"May",6:"Jun",7:"Jul",8:"Aug",9:"Sep",10:"Oct",11:"Nov",12:"Dec"}
MONTH_NAME_TO_NUM = {v: k for k, v in MONTH_NAME_MAP.items()}
TASK_COLOR_MAP = {"Lecture":"#1D4ED8","Case Report":"#0EA5E9","SNS Posting":"#EC4899","Article":"#F97316","Webinar":"#22C55E","Testimonial":"#6366F1"}
STATUS_COLORS = {"TBD": "#9CA3AF", "Planned": "#3B82F6", "On Progress": "#F59E0B", "Done": "#10B981"}
