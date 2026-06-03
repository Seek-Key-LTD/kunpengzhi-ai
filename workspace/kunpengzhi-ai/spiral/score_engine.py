"""
BYOK 评分引擎
"""

import json
import time
import hashlib
from dataclasses import dataclass, asdict
from typing import Optional

SCORE_WEIGHTS = {
    "礼分": 1.0,
    "乐分": 1.0,
    "螺旋一致": 1.5,
}
MAX_SCORE = 10.0

@dataclass
class Vote:
    vote_id: str
    voter_key_hash: str
    seat_id: str
    dimension: str
    score: float
    timestamp: float

@dataclass
class SeatScore:
    seat_id: str
    li_score: float = 0.0
    yue_score: float = 0.0
    spiral_score: float = 0.0
    vote_count: int = 0

class BYOKScoreEngine:
    def __init__(self, storage_path: str = "scores.jsonl"):
        self.storage_path = storage_path
        self._votes: list[Vote] = []
        self._seat_scores: dict[str, SeatScore] = {}

    def _hash_key(self, key: str) -> str:
        return hashlib.sha256(key.encode()).hexdigest()[:16]

    def _vote_id(self, voter_key: str, seat_id: str, dim: str, ts: float) -> str:
        raw = f"{voter_key}:{seat_id}:{dim}:{ts}"
        return hashlib.sha256(raw.encode()).hexdigest()[:12]

    def vote(self, voter_key: str, seat_id: str, dimension: str, score: float) -> Optional[Vote]:
        if dimension not in SCORE_WEIGHTS:
            return None
        if not (0 <= score <= MAX_SCORE):
            return None
        ts = time.time()
        vid = self._vote_id(voter_key, seat_id, dimension, ts)
        vhash = self._hash_key(voter_key)
        vote = Vote(vote_id=vid, voter_key_hash=vhash, seat_id=seat_id,
                    dimension=dimension, score=score, timestamp=ts)
        self._votes.append(vote)
        self._update_seat(seat_id, dimension, score)
        self._persist(vote)
        return vote

    def _update_seat(self, seat_id: str, dimension: str, score: float):
        if seat_id not in self._seat_scores:
            self._seat_scores[seat_id] = SeatScore(seat_id=seat_id)
        ss = self._seat_scores[seat_id]
        ss.vote_count += 1
        field_map = {"礼分": "li_score", "乐分": "yue_score", "螺旋一致": "spiral_score"}
        field = field_map[dimension]
        current = getattr(ss, field)
        setattr(ss, field, (current * (ss.vote_count - 1) + score) / ss.vote_count)

    def total_score(self, seat_id: str) -> float:
        ss = self._seat_scores.get(seat_id)
        if not ss:
            return 0.0
        return ss.li_score * ss.yue_score * ss.spiral_score

    def get_scores(self) -> dict:
        return {
            seat_id: {
                "li": round(ss.li_score, 3),
                "yue": round(ss.yue_score, 3),
                "spiral": round(ss.spiral_score, 3),
                "total": round(self.total_score(seat_id), 3),
                "votes": ss.vote_count,
            }
            for seat_id, ss in self._seat_scores.items()
        }

    def _persist(self, vote: Vote):
        with open(self.storage_path, "a") as f:
            f.write(json.dumps(asdict(vote)) + "\n")

    def load(self):
        try:
            with open(self.storage_path) as f:
                for line in f:
                    v = Vote(**json.loads(line))
                    self._votes.append(v)
                    self._update_seat(v.seat_id, v.dimension, v.score)
        except FileNotFoundError:
            pass