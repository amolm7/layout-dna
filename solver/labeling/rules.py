ROLE_KEYWORDS = {
    "headline": ("title", "headline", "heading"),
    "logo": ("logo", "brand"),
    "cta": ("button", "cta", "shop", "register"),
}


def infer_role(name: str | None) -> str:
    normalized = (name or "").lower()
    for role, keywords in ROLE_KEYWORDS.items():
        if any(keyword in normalized for keyword in keywords):
            return role
    return "unknown"
