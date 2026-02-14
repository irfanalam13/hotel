def system_policy_prompt() -> str:
    return (
        "You are a hotel front-desk assistant.\n"
        "Rules:\n"
        "- Never ask for or reveal card numbers, passwords, OTPs.\n"
        "- Do not provide legal/medical advice.\n"
        "- If request involves refund exceptions, upgrades, discounts, or policy override, suggest escalation.\n"
        "- Keep tone polite and concise.\n"
        "- Use only the provided policies/FAQs/templates as sources.\n"
        "- If uncertain, say you are not sure and ask to confirm with manager.\n"
    )

def reply_prompt(user_message: str, context: str) -> str:
    return (
        f"Guest/Customer message:\n{user_message}\n\n"
        f"Allowed context (policies/FAQs/templates):\n{context}\n\n"
        "Task: Draft a helpful reply using only the allowed context.\n"
        "Return format:\n"
        "REPLY:\n<text>\n"
        "CONFIDENCE: <0..1>\n"
        "SOURCES: <comma separated ids>\n"
    )

def summarize_complaint_prompt(complaint_text: str) -> str:
    return (
        "Summarize this complaint in 3-6 bullet points. Extract themes.\n"
        "Also draft a professional response that acknowledges, apologizes, and offers next steps.\n"
        "Flag risks: legal threat, violence, self-harm, medical emergency, discrimination.\n\n"
        f"Complaint:\n{complaint_text}\n\n"
        "Return format:\n"
        "SUMMARY:\n- ...\n"
        "TAGS: tag1,tag2\n"
        "RISK_FLAGS: flag1,flag2\n"
        "SUGGESTED_RESPONSE:\n<text>\n"
    )

def summarize_review_prompt(review_text: str, rating=None) -> str:
    rating_line = f"Rating: {rating}\n" if rating is not None else ""
    return (
        "Summarize this guest review in 2-4 bullets. Extract themes and actionable improvements.\n"
        "Return format:\n"
        "SUMMARY:\n- ...\n"
        "TAGS: tag1,tag2\n\n"
        f"{rating_line}Review:\n{review_text}\n"
    )
