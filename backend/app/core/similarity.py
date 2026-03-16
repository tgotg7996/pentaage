def tanimoto(a: list[int], b: list[int]) -> float:
    set_a = set(a)
    set_b = set(b)
    if not set_a and not set_b:
        return 1.0
    union_size = len(set_a | set_b)
    intersection_size = len(set_a & set_b)
    return intersection_size / union_size
