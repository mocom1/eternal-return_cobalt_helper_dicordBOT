
def calculate_elo(winner_mmr, loser_mmr, winner_games, loser_games):
    """Elo 공식을 사용해 이긴 사람과 진 사람의 변동된 MMR을 계산합니다."""
    # 1. 두 팀의 점수 차이를 바탕으로 이길 확률 계산
    expected_win = 1 / (1 + 10 ** ((loser_mmr - winner_mmr) / 400))
    
    # 2. 판수 보정 (K-factor)
    if winner_games < 10: k_winner = 40
    elif winner_games >= 30: k_winner = 12
    else: k_winner = 20
        
    if loser_games < 10: k_loser = 40
    elif loser_games >= 30: k_loser = 12
    else: k_loser = 20

    # 3. 최종 새로운 점수 계산
    new_winner_mmr = winner_mmr + k_winner * (1 - expected_win)
    new_loser_mmr = loser_mmr + k_loser * (0 - (1 - expected_win))
    
    return round(new_winner_mmr), round(new_loser_mmr)

