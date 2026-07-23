def analyze_bug(title: str, description: str) -> dict:
    text = f"{title} {description}".lower()

    severity = determine_severity(text)
    category = determine_category(text)

    return {
        "summary": f"{title} requires investigation based on the reported behavior.",
        "severity": severity,
        "category": category,
        "possible_causes": [
            "Unexpected application state",
            "Missing or invalid data",
            "Unhandled exception",
        ],
        "recommended_steps": [
            "Review the application logs",
            "Reproduce the issue in a controlled environment",
            "Check recent code or configuration changes",
        ],
    }


def determine_severity(text: str) -> str:
    if any(phrase in text for phrase in ["data loss", "security breach", "system outage"]):
        return "Critical"
    if any(word in text for word in ["crash", "500", "failure", "unavailable"]):
        return "High"
    if any(word in text for word in ["slow", "timeout", "broken", "incorrect"]):
        return "Medium"
    return "Low"


def determine_category(text: str) -> str:
    categories = {
        "Authentication": ["login", "password", "authentication", "session"],
        "API": ["api", "endpoint", "request", "response"],
        "Frontend": ["button", "page", "layout", "screen", "dashboard"],
        "Database": ["database", "sql", "record", "query"],
        "Performance": ["performance", "slow", "latency", "timeout"],
    }

    for category, keywords in categories.items():
        if any(keyword in text for keyword in keywords):
            return category

    return "General"
