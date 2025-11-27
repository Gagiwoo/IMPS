"""
중앙 설정 파일
모든 하드코딩 값을 여기서 관리
"""

# LLM 설정
LLM_MODEL = "llama3.1"
LLM_TEMPERATURE = 0.1
LLM_TIMEOUT = 30  # 초

# 맵 설정
GRID_SIZE = 120
MAP_BOUNDS = {
    "min_lat": 33.0,
    "max_lat": 43.0,
    "min_lon": 124.0,
    "max_lon": 132.0
}

# 경로 설정
DEFAULT_SAFETY_MARGIN = 5.0  # km
DEFAULT_STPT_GAP = 10
SMOOTHING_FACTOR = 0.0002

# 공항 데이터베이스
AIRPORTS = {
    "서산(Seosan)": [36.776, 126.493],
    "오산(Osan)": [37.090, 127.030],
    "원주(Wonju)": [37.342, 127.920],
    "강릉(Gangneung)": [37.751, 128.876],
    "충주(Chungju)": [36.991, 127.926],
    "청주(Cheongju)": [36.642, 127.489],
    "대구(Daegu)": [35.871, 128.601],
    "광주(Gwangju)": [35.159, 126.852],
    "부산(Busan)": [35.179, 129.075],
    "수원(Suwon)": [37.240, 127.000],
    "사천(Sacheon)": [35.088, 128.070],
    "서울(Seoul)": [37.463, 126.924]
}

# UI 설정
MAP_CENTER = [38.0, 128.0]
MAP_ZOOM = 6
CHAT_CONTAINER_HEIGHT = 350

# 로깅
LOG_DIR = "logs"
ENABLE_LOGGING = True
