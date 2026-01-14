def calculate_confidence(
    face_similarity: float,
    face_match: bool,
    audio_matched: bool,
    liveness_passed: bool
):
    """
    Confidence Scoring (Max = 100, Pass >= 80)

    Face Recognition (Max 60):
    - Uses cosine similarity from ArcFace (0.0 → 1.0)
    - Minimum usable similarity = 0.70
    - 0.70 → 0 points
    - 0.85+ → 60 points
    - Linear interpolation in between

    Liveness Check (20):
    - Passed → +20

    Audio Challenge (20):
    - Phrase matched → +20
    """

    score = 0

    # -----------------------------
    # 1. Face similarity score
    # -----------------------------
    FACE_MIN = 0.70
    FACE_MAX = 0.80
    FACE_WEIGHT = 60

    if face_match and face_similarity >= FACE_MIN:
        if face_similarity >= FACE_MAX:
            score += FACE_WEIGHT
        else:
            normalized = (face_similarity - FACE_MIN) / (FACE_MAX - FACE_MIN)
            score += int(normalized * FACE_WEIGHT)

    # -----------------------------
    # 2. Liveness score
    # -----------------------------
    if liveness_passed:
        score += 20

    # -----------------------------
    # 3. Audio challenge score
    # -----------------------------
    if audio_matched:
        score += 20

    return score
