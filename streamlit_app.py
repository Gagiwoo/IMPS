"""
메인 Streamlit UI
v9.0 - Production Ready
"""
import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd

from modules.config import AIRPORTS, MAP_CENTER, MAP_ZOOM, CHAT_CONTAINER_HEIGHT
from modules.mission_state import MissionState, Threat
from modules.llm_brain import LLMBrain
from modules.pathfinder import AStarPathfinder, smooth_path


# ===== 페이지 설정 =====
st.set_page_config(
    page_title="IMPS v9.0",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.title("🚁 통합 임무계획 시스템 v9.0 (Production)")


# ===== 상태 초기화 =====
if "mission" not in st.session_state:
    st.session_state.mission = MissionState()

mission = st.session_state.mission


# ===== 레이아웃 =====
col_left, col_right = st.columns([1, 2])

with col_left:
    tab_ops, tab_intel, tab_debug = st.tabs(["💬 작전 통제", "⚠️ 위협 관리", "🔧 디버그"])
    
    # --- 작전 통제 탭 ---
    with tab_ops:
        with st.expander("⚙️ 미션 프로파일", expanded=True):
            p = mission.params
            
            p.start = st.selectbox("출발 기지", list(AIRPORTS.keys()), 
                                   index=list(AIRPORTS.keys()).index(p.start))
            
            st.caption("🎯 타겟 좌표")
            c1, c2 = st.columns(2)
            p.target_lat = c1.number_input("Lat", 33.0, 43.0, p.target_lat, format="%.4f")
            p.target_lon = c2.number_input("Lon", 124.0, 132.0, p.target_lon, format="%.4f")
            
            p.rtb = st.checkbox("Strike & RTB", value=p.rtb)
            p.margin = st.slider("안전 마진(km)", 0.0, 50.0, p.margin)
            p.stpt_gap = st.slider("STPT 표시 간격", 1, 50, p.stpt_gap)
            
            if st.button("🔄 업데이트", type="primary"):
                st.rerun()
        
        # 채팅 인터페이스
        chat_container = st.container(height=CHAT_CONTAINER_HEIGHT)
        for msg in mission.chat_history:
            with chat_container.chat_message(msg["role"]):
                st.write(msg["content"])
        
        if user_input := st.chat_input("명령 입력 (예: STPT 줄여줘)"):
            mission.add_chat_message("user", user_input)
            
            with chat_container.chat_message("user"):
                st.write(user_input)
            
            with st.spinner("🧠 AI 분석 중..."):
                brain = LLMBrain()
                result = brain.parse_tactical_command(user_input, mission.params.to_dict())
                
                # 파라미터 업데이트
                if result["action"] == "UPDATE":
                    u = result["update_params"]
                    if u.get("safety_margin_km") is not None:
                        mission.params.margin = u["safety_margin_km"]
                    if u.get("rtb") is not None:
                        mission.params.rtb = u["rtb"]
                    if u.get("stpt_gap") is not None:
                        mission.params.stpt_gap = u["stpt_gap"]
                    if u.get("waypoint_name"):
                        mission.params.waypoint = u["waypoint_name"]
                
                ai_msg = result["response_text"]
                mission.add_chat_message("assistant", ai_msg)
                
                with chat_container.chat_message("assistant"):
                    st.write(ai_msg)
                
                st.rerun()
    
    # --- 위협 관리 탭 ---
    with tab_intel:
        st.subheader("위협 관리")
        
        add_type = st.radio("유형", ["원형 (SAM)", "사각형 (NFZ)"], horizontal=True)
        t_name = st.text_input("명칭", value="Threat")
        
        if add_type == "원형 (SAM)":
            c1, c2 = st.columns(2)
            t_lat = c1.number_input("Lat", 33.0, 43.0, 38.0)
            t_lon = c2.number_input("Lon", 124.0, 132.0, 127.0)
            t_rad = st.slider("Radius(km)", 5, 50, 20)
            
            if st.button("➕ SAM 추가"):
                mission.add_threat(Threat(
                    name=t_name, type="SAM", 
                    lat=t_lat, lon=t_lon, radius_km=t_rad
                ))
                st.rerun()
        else:
            c1, c2 = st.columns(2)
            l_min = c1.number_input("Min Lat", 33.0, 43.0, 37.5)
            l_max = c2.number_input("Max Lat", 33.0, 43.0, 37.8)
            ln_min = c1.number_input("Min Lon", 124.0, 132.0, 127.5)
            ln_max = c2.number_input("Max Lon", 124.0, 132.0, 127.8)
            
            if st.button("➕ NFZ 추가"):
                mission.add_threat(Threat(
                    name=t_name, type="NFZ",
                    lat_min=l_min, lat_max=l_max,
                    lon_min=ln_min, lon_max=ln_max
                ))
                st.rerun()
        
        st.divider()
        
        # 위협 목록
        if mission.threats:
            threat_df = pd.DataFrame([t.to_dict() for t in mission.threats])
            st.dataframe(threat_df, hide_index=True)
            
            del_name = st.selectbox("삭제할 위협", [t.name for t in mission.threats])
            if st.button("🗑️ 삭제"):
                mission.remove_threat(del_name)
                st.rerun()
    
    # --- 디버그 탭 ---
    with tab_debug:
        st.subheader("디버그 & 실험 재현")
        
        save_name = st.text_input("시나리오 이름", value="scenario_01.json")
        if st.button("💾 현재 상태 저장"):
            mission.save_to_file(save_name)
            st.success(f"✅ {save_name} 저장 완료")
        
        st.caption("저장된 시나리오는 `logs/` 폴더에서 확인 가능")
        
        st.divider()
        st.json(mission.params.to_dict())


# ===== 경로 계산 및 지도 시각화 =====
with col_right:
    pathfinder = AStarPathfinder()
    
    start_coord = AIRPORTS[mission.params.start]
    target_coord = [mission.params.target_lat, mission.params.target_lon]
    
    threats_dict = [t.to_dict() for t in mission.threats]
    
    # Ingress 경로
    wp_coord = None
    if mission.params.waypoint and mission.params.waypoint in AIRPORTS:
        wp_coord = AIRPORTS[mission.params.waypoint]
    
    raw_in = []
    if wp_coord:
        p1 = pathfinder.find_path(start_coord, wp_coord, threats_dict, mission.params.margin)
        p2 = pathfinder.find_path(wp_coord, target_coord, threats_dict, mission.params.margin)
        if p1 and p2:
            raw_in = p1 + p2[1:]
    else:
        raw_in = pathfinder.find_path(start_coord, target_coord, threats_dict, mission.params.margin)
    
    final_in = smooth_path(raw_in) if raw_in else []
    
    # Egress 경로 (RTB)
    final_out = []
    if mission.params.rtb:
        raw_out = pathfinder.find_path(target_coord, start_coord, threats_dict, mission.params.margin)
        final_out = smooth_path(raw_out) if raw_out else []
    
    # 지도 생성
    m = folium.Map(location=MAP_CENTER, zoom_start=MAP_ZOOM)
    
    # 공항 마커
    for name, coord in AIRPORTS.items():
        color = "blue" if name == mission.params.start else "gray"
        folium.Marker(
            coord, 
            icon=folium.Icon(color=color, icon="plane"),
            tooltip=name
        ).add_to(m)
    
    # 타겟 마커
    folium.Marker(
        target_coord,
        icon=folium.Icon(color="red", icon="crosshairs", prefix="fa"),
        tooltip=f"TARGET: {mission.params.target_name}"
    ).add_to(m)
    
    # 위협 시각화
    for t in mission.threats:
        if t.type == "SAM":
            folium.Circle(
                [t.lat, t.lon],
                radius=t.radius_km * 1000,
                color="crimson",
                fill=True,
                fill_opacity=0.3,
                tooltip=t.name
            ).add_to(m)
        elif t.type == "NFZ":
            folium.Rectangle(
                [[t.lat_min, t.lon_min], [t.lat_max, t.lon_max]],
                color="orange",
                fill=True,
                fill_opacity=0.3,
                tooltip=t.name
            ).add_to(m)
    
    # 경로 시각화
    if final_in:
        folium.PolyLine(final_in, color="blue", weight=4, opacity=0.8).add_to(m)
    
    if final_out:
        folium.PolyLine(final_out, color="orange", weight=4, dash_array="5, 5", opacity=0.8).add_to(m)
    
    # 지도 표시
    st_folium(m, width="100%", height=700)
    
    # STPT 리스트
    if final_in:
        st.divider()
        st.subheader("📋 Steer Point List")
        
        gap = mission.params.stpt_gap
        data_in = [
            {"Type": "Ingress", "Seq": i+1, "Lat": f"{p[0]:.4f}", "Lon": f"{p[1]:.4f}"}
            for i, p in enumerate(final_in[::gap])
        ]
        
        data_out = []
        if final_out:
            data_out = [
                {"Type": "Egress", "Seq": i+1, "Lat": f"{p[0]:.4f}", "Lon": f"{p[1]:.4f}"}
                for i, p in enumerate(final_out[::gap])
            ]
        
        stpt_df = pd.DataFrame(data_in + data_out)
        st.dataframe(stpt_df, use_container_width=True)
        
        # CSV 다운로드
        csv = stpt_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            "📥 STPT CSV 다운로드",
            csv,
            "steer_points.csv",
            "text/csv"
        )
    else:
        st.warning("⚠️ 경로를 찾을 수 없습니다. 위협 마진을 조정하거나 목표 좌표를 변경하세요.")
