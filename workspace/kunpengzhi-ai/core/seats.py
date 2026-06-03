"""
八席位卦象拓扑定义
"""

from enum import Enum
from typing import Dict, List

class SeatRole(Enum):
    PRO = "pro"
    CON = "con"
    JUDGE = "judge"

# 8席位完整定义
SEATS = {
    "seat_1": {
        "id": "seat_1",
        "name": "吕洞宾",
        "trigram": "乾",
        "gua": "☰",
        "note": "G",
        "frequency": 196.0,
        "role": SeatRole.PRO,
        "sanhe": ["子", "辰", "申"],
        "quality": "纯阳剑意",
    },
    "seat_2": {
        "id": "seat_2",
        "name": "何仙姑",
        "trigram": "坤",
        "gua": "☷",
        "note": "C",
        "frequency": 261.63,
        "role": SeatRole.PRO,
        "sanhe": ["亥", "卯", "未"],
        "quality": "柔中带刚",
    },
    "seat_3": {
        "id": "seat_3",
        "name": "张果老",
        "trigram": "艮",
        "gua": "☶",
        "note": "D",
        "frequency": 293.66,
        "role": SeatRole.CON,
        "sanhe": ["寅", "午", "戌"],
        "quality": "老谋深算",
    },
    "seat_4": {
        "id": "seat_4",
        "name": "韩湘子",
        "trigram": "兑",
        "gua": "☱",
        "note": "A",
        "frequency": 440.0,
        "role": SeatRole.CON,
        "sanhe": ["巳", "酉", "丑"],
        "quality": "清越肃杀",
    },
    "seat_5": {
        "id": "seat_5",
        "name": "汉钟离",
        "trigram": "离",
        "gua": "☲",
        "note": "Eb",
        "frequency": 311.13,
        "role": SeatRole.PRO,
        "sanhe": ["巳", "酉", "丑"],
        "quality": "重剑无锋",
    },
    "seat_6": {
        "id": "seat_6",
        "name": "蓝采和",
        "trigram": "坎",
        "gua": "☵",
        "note": "Ab",
        "frequency": 415.30,
        "role": SeatRole.CON,
        "sanhe": ["子", "辰", "申"],
        "quality": "嬉笑怒骂",
    },
    "seat_7": {
        "id": "seat_7",
        "name": "曹国舅",
        "trigram": "震",
        "gua": "☳",
        "note": "Bb",
        "frequency": 466.16,
        "role": SeatRole.PRO,
        "sanhe": ["亥", "卯", "未"],
        "quality": "权柄在握",
    },
    "seat_8": {
        "id": "seat_8",
        "name": "铁拐李",
        "trigram": "巽",
        "gua": "☴",
        "note": "Db",
        "frequency": 554.37,
        "role": SeatRole.CON,
        "sanhe": ["寅", "午", "戌"],
        "quality": "壶中乾坤",
    },
}

# 根音在螺旋谱上的位置（度数，0-11，基于12平均律）
ROOT_OFFSET = {
    "G":  0,
    "C":  5,
    "D":  2,
    "A":  9,
    "Eb": 3,
    "Ab": 8,
    "Bb": 10,
    "Db": 1,
}

# 五声音阶度数（宫商角徵羽，排除偏音）
PENTATONIC_DEGREES = {
    note: [0, 2, 4, 7, 9] for note in ROOT_OFFSET
}

def get_seat(seat_id: str) -> Dict:
    return SEATS.get(seat_id)

def get_seats_by_role(role: SeatRole) -> List[Dict]:
    return [s for s in SEATS.values() if s["role"] == role]

def get_pro_seats() -> List[Dict]:
    return get_seats_by_role(SeatRole.PRO)

def get_con_seats() -> List[Dict]:
    return get_seats_by_role(SeatRole.CON)