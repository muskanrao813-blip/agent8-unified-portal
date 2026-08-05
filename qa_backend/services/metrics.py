"""Pure functions to compute metrics from diarized transcript segments."""


def compute_talk_ratios(segments: list[dict]) -> dict:
    """Compute talk-time ratios for dietician vs patient."""
    dietician_time = 0.0
    patient_time = 0.0

    for seg in segments:
        duration = (seg.get("end_s", 0) - seg.get("start_s", 0)) or 0
        speaker = seg.get("speaker", "").lower()

        if "dietician" in speaker or "doctor" in speaker or "speaker_0" in speaker:
            dietician_time += duration
        elif "patient" in speaker or "speaker_1" in speaker:
            patient_time += duration

    total_time = dietician_time + patient_time
    if total_time == 0:
        return {"dietician_pct": 0.0, "patient_pct": 0.0}

    return {
        "dietician_pct": round((dietician_time / total_time) * 100, 2),
        "patient_pct": round((patient_time / total_time) * 100, 2),
    }


def compute_interruptions(segments: list[dict], gap_threshold_s: float = 2.0) -> int:
    """Count interruptions (overlapping or near-overlapping speech turns)."""
    if len(segments) < 2:
        return 0

    interruptions = 0
    for i in range(len(segments) - 1):
        current = segments[i]
        next_seg = segments[i + 1]

        gap = next_seg.get("start_s", 0) - current.get("end_s", 0)

        if gap < 0 or (gap >= 0 and gap < gap_threshold_s):
            current_speaker = current.get("speaker", "").lower()
            next_speaker = next_seg.get("speaker", "").lower()

            if current_speaker != next_speaker and gap < gap_threshold_s:
                interruptions += 1

    return interruptions


def compute_response_latency(segments: list[dict]) -> float:
    """Compute average response latency (gap between speaker turns)."""
    if len(segments) < 2:
        return 0.0

    gaps = []
    for i in range(len(segments) - 1):
        current = segments[i]
        next_seg = segments[i + 1]

        gap = next_seg.get("start_s", 0) - current.get("end_s", 0)
        if gap >= 0:
            gaps.append(gap)

    return round(sum(gaps) / len(gaps), 2) if gaps else 0.0


def compute_silence_pct(segments: list[dict], total_duration: float) -> float:
    """Compute percentage of call that is silence (no speech)."""
    if not segments or total_duration == 0:
        return 0.0

    speech_time = 0.0
    for seg in segments:
        duration = (seg.get("end_s", 0) - seg.get("start_s", 0)) or 0
        speech_time += duration

    silence_time = total_duration - speech_time
    return round((silence_time / total_duration) * 100, 2) if silence_time > 0 else 0.0


def compute_time_to_first_plan(segments: list[dict]) -> float | None:
    """Find timestamp of first prescriptive/plan-related statement."""
    keywords = ["diet", "plan", "eat", "food", "meal", "protein", "carb", "fat", "calories", "prescription"]

    for seg in segments:
        text = seg.get("text", "").lower()
        if any(kw in text for kw in keywords):
            return round(seg.get("start_s", 0), 2)

    return None


def compute_off_topic_pct(segments: list[dict], off_topic_labels: list[str] = None) -> float:
    """Compute percentage of non-clinical talk (placeholder for v2)."""
    # v2: implement classifier to detect off-topic content
    # For now: return 0 unless off_topic_labels provided
    if not off_topic_labels:
        return 0.0

    off_topic_time = 0.0
    for seg in segments:
        if seg.get("label") in off_topic_labels:
            duration = (seg.get("end_s", 0) - seg.get("start_s", 0)) or 0
            off_topic_time += duration

    total_time = sum((seg.get("end_s", 0) - seg.get("start_s", 0)) for seg in segments)
    if total_time == 0:
        return 0.0

    return round((off_topic_time / total_time) * 100, 2)


def count_patient_words(segments: list[dict]) -> int:
    """Count total words spoken by patient."""
    patient_text = ""
    for seg in segments:
        speaker = seg.get("speaker", "").lower()
        if "patient" in speaker or "speaker_1" in speaker:
            patient_text += " " + seg.get("text", "")

    return len(patient_text.split())
