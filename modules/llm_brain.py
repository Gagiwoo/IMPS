"""
LLM Brain 모듈 - 에러 처리 및 검증 강화
"""
import ollama
import json
from typing import Dict, Optional
from modules.config import LLM_MODEL, LLM_TEMPERATURE, LLM_TIMEOUT, AIRPORTS


class LLMBrain:
    """LLM 인터페이스 클래스"""
    
    def __init__(self, model_name: str = LLM_MODEL):
        self.model = model_name
        self.temperature = LLM_TEMPERATURE
        
    def parse_tactical_command(self, user_msg: str, current_state: Dict) -> Dict:
        """
        자연어 명령 파싱
        
        Args:
            user_msg: 사용자 입력
            current_state: 현재 미션 상태
            
        Returns:
            파싱된 JSON 응답 (action, update_params, response_text)
        """
        state_desc = (
            f"Margin: {current_state['margin']}km, "
            f"RTB: {current_state['rtb']}, "
            f"Waypoint: {current_state['waypoint']}, "
            f"STPT_Gap: {current_state['stpt_gap']}"
        )
        
        system_prompt = f"""
You are a Mission Planning AI. The user will give orders about flight path or settings.
Current State: {state_desc}

Available Actions:
1. Safety Margin: Adjust 'safety_margin_km' (float, 0.0~50.0).
2. RTB: Set 'rtb' (bool) to true/false.
3. Waypoint: Set 'waypoint_name' (must be exactly one of {list(AIRPORTS.keys())} or null).
4. Steer Points: Adjust 'stpt_gap' (int, 1~50). Higher value = FEWER points (less dense). Lower = MORE points.

**Validation Rules:**
- If waypoint_name is provided, it MUST exist in the airport list above. Otherwise set to null.
- safety_margin_km must be between 0.0 and 50.0.
- stpt_gap must be between 1 and 50.
- If user input is unclear or impossible, set action to "CHAT" and explain the issue.

Output JSON ONLY:
{{
    "action": "UPDATE" or "CHAT",
    "update_params": {{
        "safety_margin_km": float/null, 
        "rtb": bool/null, 
        "waypoint_name": string/null,
        "stpt_gap": int/null
    }},
    "response_text": "A brief, professional confirmation in Korean (Military tone)."
}}
"""
        
        try:
            response = ollama.chat(
                model=self.model,
                messages=[
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': user_msg}
                ],
                format='json',
                options={'temperature': self.temperature}
            )
            
            result = json.loads(response['message']['content'])
            
            # 검증 단계
            validated = self._validate_output(result)
            return validated
            
        except ollama.ResponseError as e:
            return {
                "action": "CHAT",
                "response_text": f"❌ LLM 서버 오류: {str(e)}. Ollama가 실행 중인지 확인하세요.",
                "update_params": {}
            }
        except json.JSONDecodeError as e:
            return {
                "action": "CHAT",
                "response_text": f"❌ LLM 응답 파싱 실패: {str(e)}",
                "update_params": {}
            }
        except Exception as e:
            return {
                "action": "CHAT",
                "response_text": f"❌ 알 수 없는 오류: {str(e)}",
                "update_params": {}
            }
    
    def _validate_output(self, result: Dict) -> Dict:
        """LLM 출력 검증"""
        params = result.get("update_params", {})
        
        # Safety Margin 범위 체크
        if params.get("safety_margin_km") is not None:
            margin = params["safety_margin_km"]
            if not (0.0 <= margin <= 50.0):
                params["safety_margin_km"] = max(0.0, min(50.0, margin))
        
        # STPT Gap 범위 체크
        if params.get("stpt_gap") is not None:
            gap = params["stpt_gap"]
            if not (1 <= gap <= 50):
                params["stpt_gap"] = max(1, min(50, gap))
        
        # Waypoint 존재 여부 체크
        if params.get("waypoint_name") and params["waypoint_name"] not in AIRPORTS:
            params["waypoint_name"] = None
            result["response_text"] += " (⚠️ 존재하지 않는 공항명은 무시되었습니다)"
        
        result["update_params"] = params
        return result
