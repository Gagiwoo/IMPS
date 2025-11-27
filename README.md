# 🚁 Intelligent Mission Planning System (IMPS) v9.0

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)](https://streamlit.io/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## 📖 Overview

폐쇄망 환경에서 작동하는 **LLM 기반 전술 임무계획 시스템**입니다.  
자연어 명령을 해석하여 위협 회피 경로를 실시간으로 생성합니다.

### 핵심 특징
- ✅ **Hybrid Architecture**: LLM(두뇌) + A* Pathfinding(계산기)
- ✅ **On-premise**: Ollama 기반 로컬 LLM 구동
- ✅ **Real-time**: 동적 위협 추가 시 즉시 경로 재계산
- ✅ **Reproducible**: 실험 시나리오 저장/복원 기능

---

## 🚀 Quick Start

### 1. 설치
\`\`\`bash
pip install -r requirements.txt
\`\`\`

### 2. Ollama 설치 및 모델 다운로드
\`\`\`bash
# Ollama 설치 (https://ollama.ai)
ollama pull llama3.1
\`\`\`

### 3. 실행
\`\`\`bash
streamlit run streamlit_app.py
\`\`\`

---

## 📁 Project Structure

\`\`\`
mission_planner_v9/
├── modules/           # 핵심 모듈
│   ├── config.py      # 설정 상수
│   ├── llm_brain.py   # LLM 인터페이스
│   ├── pathfinder.py  # A* 경로탐색
│   └── mission_state.py # 상태 관리
├── tests/             # 유닛 테스트
├── logs/              # 실험 로그
├── streamlit_app.py   # 메인 UI
└── README.md
\`\`\`

---

## 🔬 Research Use

### 실험 재현성
모든 미션 시나리오는 JSON으로 저장 가능:
\`\`\`python
mission.save_to_file("scenario_01.json")
\`\`\`

### 논문 작성 시 활용
- **Figure**: Folium 지도 캡처 (경로 시각화)
- **Table**: STPT CSV 데이터
- **Supplementary**: `logs/` 폴더의 JSON 시나리오

---

## 📧 Contact
- Email: ksain1@ajou.ac.kr