"""전적 데이터를 분석해 전체 요약과 주 실험체(메인 캐릭터)를 추천하는 로직."""
from dataclasses import dataclass, field


@dataclass
class CharacterStat:
    character_num: int
    games: int = 0
    wins: int = 0
    top3: int = 0
    kill_sum: int = 0
    rank_sum: int = 0

    @property
    def win_rate(self) -> float:
        return self.wins / self.games if self.games else 0.0

    @property
    def top3_rate(self) -> float:
        return self.top3 / self.games if self.games else 0.0

    @property
    def avg_rank(self) -> float:
        return self.rank_sum / self.games if self.games else 0.0

    @property
    def avg_kills(self) -> float:
        return self.kill_sum / self.games if self.games else 0.0

    @property
    def score(self) -> float:
        # 순위는 1등이 최상, 보통 한 판에 최대 18명 내외가 참가하므로 18을 기준으로 정규화.
        rank_score = max(0.0, (18 - self.avg_rank) / 17)
        return self.win_rate * 0.5 + self.top3_rate * 0.3 + rank_score * 0.2


@dataclass
class OverallStat:
    games: int = 0
    wins: int = 0
    top3: int = 0
    kill_sum: int = 0
    rank_sum: int = 0
    by_character: dict[int, CharacterStat] = field(default_factory=dict)

    @property
    def win_rate(self) -> float:
        return self.wins / self.games if self.games else 0.0

    @property
    def top3_rate(self) -> float:
        return self.top3 / self.games if self.games else 0.0

    @property
    def avg_rank(self) -> float:
        return self.rank_sum / self.games if self.games else 0.0

    @property
    def avg_kills(self) -> float:
        return self.kill_sum / self.games if self.games else 0.0


def analyze_games(games: list[dict]) -> OverallStat:
    overall = OverallStat()
    for g in games:
        char_num = g.get("characterNum")
        rank = g.get("gameRank", 0)
        kills = g.get("playerKill", 0)
        is_win = rank == 1
        is_top3 = rank != 0 and rank <= 3

        overall.games += 1
        overall.wins += int(is_win)
        overall.top3 += int(is_top3)
        overall.kill_sum += kills
        overall.rank_sum += rank

        if char_num is None:
            continue
        cs = overall.by_character.setdefault(char_num, CharacterStat(char_num))
        cs.games += 1
        cs.wins += int(is_win)
        cs.top3 += int(is_top3)
        cs.kill_sum += kills
        cs.rank_sum += rank

    return overall


def recommend_characters(
    overall: OverallStat, min_games: int = 3, top_n: int = 3
) -> list[CharacterStat]:
    candidates = [cs for cs in overall.by_character.values() if cs.games >= min_games]
    if not candidates:
        # 최소 판수를 채운 캐릭터가 없으면 기준을 낮춰서라도 추천.
        candidates = list(overall.by_character.values())
    candidates.sort(key=lambda cs: cs.score, reverse=True)
    return candidates[:top_n]
