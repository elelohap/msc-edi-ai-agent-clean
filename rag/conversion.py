def get_conversion_nudge(question: str, answerable: bool) -> str:
    
   if not answerable:
        return (
            "I may not have this specific detail in my current sources. "
            "If you tell me what you’re deciding (fit, curriculum, projects, admissions), "
            "I can guide you using what’s available in the programme information."
        )

    # otherwise: your normal “high conversion” nudges
    q = (question or "").lower()
    if "apply" in q or "admission" in q or "deadline" in q:
        return "If you'd like, I can guide you through what to prepare for the application."
    if "project" in q:
        return "If you share your interests (e.g., sustainability, health, AI), I can suggest what kinds of projects may align."
    return "If you tell me your background and goals, I can help you evaluate fit using the programme details."
