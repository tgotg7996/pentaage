def total_score(max_similarity: float, top3_avg_similarity: float) -> int:
    base = max_similarity * 60
    composite = top3_avg_similarity * 40
    return min(int(base + composite), 100)
