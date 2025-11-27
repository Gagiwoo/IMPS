"""
A* 경로탐색 엔진 - 최적화 및 디버깅 강화
"""
import math
import heapq
import numpy as np
from scipy.interpolate import splprep, splev
from typing import List, Tuple, Optional
from modules.config import GRID_SIZE, MAP_BOUNDS, SMOOTHING_FACTOR


class AStarPathfinder:
    """A* 알고리즘 기반 경로탐색"""
    
    def __init__(self, grid_size: int = GRID_SIZE):
        self.grid_size = grid_size
        self.bounds = [
            MAP_BOUNDS["min_lat"],
            MAP_BOUNDS["max_lat"],
            MAP_BOUNDS["min_lon"],
            MAP_BOUNDS["max_lon"]
        ]
        
    def to_grid(self, lat: float, lon: float) -> Tuple[int, int]:
        """위경도 → 그리드 좌표 변환"""
        min_lat, max_lat, min_lon, max_lon = self.bounds
        
        if not (min_lat <= lat <= max_lat and min_lon <= lon <= max_lon):
            return -1, -1
        
        y = int((lat - min_lat) / ((max_lat - min_lat) / self.grid_size))
        x = int((lon - min_lon) / ((max_lon - min_lon) / self.grid_size))
        
        # 경계 체크
        y = max(0, min(self.grid_size - 1, y))
        x = max(0, min(self.grid_size - 1, x))
        
        return x, y
    
    def to_latlon(self, x: int, y: int) -> Tuple[float, float]:
        """그리드 좌표 → 위경도 변환"""
        min_lat, max_lat, min_lon, max_lon = self.bounds
        
        lat = min_lat + (y * ((max_lat - min_lat) / self.grid_size))
        lon = min_lon + (x * ((max_lon - min_lon) / self.grid_size))
        
        return lat, lon
    
    def is_collision(self, lat: float, lon: float, threats: List[dict], margin: float) -> bool:
        """위협 충돌 체크"""
        margin_deg = margin / 111.0  # km → 위도 degree 근사
        
        for t in threats:
            if t['type'] == "SAM":
                dist_km = math.sqrt(
                    ((lat - t['lat']) * 111) ** 2 + 
                    ((lon - t['lon']) * 111 * math.cos(math.radians(lat))) ** 2
                )
                if dist_km < (t['radius_km'] + margin):
                    return True
                    
            elif t['type'] == "NFZ":
                if ((t['lat_min'] - margin_deg <= lat <= t['lat_max'] + margin_deg) and
                    (t['lon_min'] - margin_deg <= lon <= t['lon_max'] + margin_deg)):
                    return True
        
        return False
    
    def find_path(
        self,
        start: List[float],
        end: List[float],
        threats: List[dict],
        safety_margin: float
    ) -> List[Tuple[float, float]]:
        """
        A* 경로탐색
        
        Returns:
            경로 리스트 [(lat, lon), ...] 또는 빈 리스트 (실패시)
        """
        start_grid = self.to_grid(start[0], start[1])
        end_grid = self.to_grid(end[0], end[1])
        
        if start_grid == (-1, -1) or end_grid == (-1, -1):
            return []
        
        # A* 초기화
        open_set = []
        heapq.heappush(open_set, (0, start_grid))
        came_from = {}
        g_score = {start_grid: 0}
        
        # 8방향 이동
        directions = [
            (0, 1), (0, -1), (1, 0), (-1, 0),
            (1, 1), (1, -1), (-1, 1), (-1, -1)
        ]
        
        nodes_explored = 0  # 디버깅용
        
        while open_set:
            current = heapq.heappop(open_set)[1]
            nodes_explored += 1
            
            # 목표 도달
            if current == end_grid:
                path = []
                while current in came_from:
                    path.append(self.to_latlon(current[0], current[1]))
                    current = came_from[current]
                path.append(start)
                return path[::-1]
            
            # 이웃 탐색
            for dx, dy in directions:
                neighbor = (current[0] + dx, current[1] + dy)
                
                # 그리드 범위 체크
                if not (0 <= neighbor[0] < self.grid_size and 
                        0 <= neighbor[1] < self.grid_size):
                    continue
                
                n_lat, n_lon = self.to_latlon(neighbor[0], neighbor[1])
                
                # 위협 충돌 체크
                if self.is_collision(n_lat, n_lon, threats, safety_margin):
                    continue
                
                # 비용 계산 (대각선은 √2)
                move_cost = math.sqrt(dx**2 + dy**2)
                tentative_g_score = g_score[current] + move_cost
                
                if neighbor not in g_score or tentative_g_score < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g_score
                    
                    # 휴리스틱 (유클리드 거리)
                    h = math.sqrt(
                        (neighbor[0] - end_grid[0]) ** 2 + 
                        (neighbor[1] - end_grid[1]) ** 2
                    )
                    
                    f_score = tentative_g_score + h
                    heapq.heappush(open_set, (f_score, neighbor))
        
        # 경로를 찾지 못함
        print(f"⚠️ 경로탐색 실패: {nodes_explored}개 노드 탐색")
        return []


def smooth_path(path_coords: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
    """
    B-Spline을 이용한 경로 평탄화
    
    Args:
        path_coords: 원본 경로
        
    Returns:
        평탄화된 경로
    """
    if not path_coords or len(path_coords) < 3:
        return path_coords
    
    try:
        lat = [p[0] for p in path_coords]
        lon = [p[1] for p in path_coords]
        
        # 중복 제거
        clean_lat, clean_lon = [], []
        for i in range(len(lat)):
            if i == 0 or (lat[i] != lat[i-1] or lon[i] != lon[i-1]):
                clean_lat.append(lat[i])
                clean_lon.append(lon[i])
        
        if len(clean_lat) < 3:
            return path_coords
        
        # B-Spline 보간
        tck, u = splprep([clean_lat, clean_lon], s=SMOOTHING_FACTOR, per=False)
        u_new = np.linspace(u.min(), u.max(), len(path_coords) * 5)
        new_lat, new_lon = splev(u_new, tck)
        
        return list(zip(new_lat, new_lon))
        
    except Exception as e:
        print(f"⚠️ 경로 평탄화 실패: {str(e)}")
        return path_coords
