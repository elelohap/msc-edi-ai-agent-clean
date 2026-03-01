def get_conversion_nudge(question: str) -> str:
    q = (question or "").lower()

    def has(*k):
        return any(x in q for x in k)

    # --- Late stage (high intent) ---
    if has("apply", "admission", "deadline", "requirement"):
        return "If you're ready, I can guide you through the application process step by step."

    # --- Career / value ---
    if has("career", "job", "outcome"):
        return "If helpful, I can show how EDI aligns with your career goals."

    # --- Fit / suitability ---
    if has("suitable", "fit", "background"):
        return "If you like, I can help assess how your background fits the EDI programme."

    # --- Projects / experience ---
    if has("project", "projects", "learning"):
        return "I can also walk you through a typical student journey if you're interested."

    # --- Workload / difficulty ---
    if has("workload", "stress", "cope"):
        return "I can share how students typically manage the workload if that helps."

    # --- Default (early stage) ---
    return "Let me know if you'd like to explore how this programme fits your goals."
