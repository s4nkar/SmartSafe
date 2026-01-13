

def calculate_confidence(face_distance, audio_matched, liveness_passed):
    """
    Your custom scoring logic.
    DeepFace Cosine distance: Lower is better (0 = exact match).
    Threshold usually around 0.4 for ArcFace/FaceNet.
    """
    score = 0
    
    # 1. Face Match Logic (Inverted distance)
    # If distance is 0.2, match quality is roughly 80%
    face_score = max(0, (1.0 - face_distance) * 100)
    
    if face_distance < 0.4: # Hard threshold for "Is this the person?"
        score += 50
        # Bonus for high accuracy
        if face_distance < 0.2:
            score += 10
    
    # 2. Liveness/Audio Logic
    if liveness_passed:
        score += 20
    if audio_matched:
        score += 20
        
    return score