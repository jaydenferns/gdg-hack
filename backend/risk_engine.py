"""Explainable, local-first conversational risk scoring for the Guardian AI MVP."""
from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class Analysis:
    risk_score: int
    risk_level: str
    language: str
    indicators: list[str]
    explanation: str
    recommended_action: str


SIGNALS: dict[str, tuple[list[str], int, str]] = {
    "Age targeting": ([r"\bhow old\b", r"\bage\b", r"kitne saal", r"उम्र", r"वय"], 14, "The message probes the user's age."),
    "Age-related flattery": ([r"mature for your age", r"so mature", r"age se.*mature", r"समझदार"], 8, "The speaker uses age-related flattery."),
    "Boundary testing": ([r"parents?.*(check|phone)", r"who.*home", r"alone\b", r"घर.*कौन"], 8, "The speaker is testing trusted-adult supervision."),
    "Secrecy request": ([r"don'?t tell", r"keep.*secret", r"mat batana", r"मत बताना", r"सांगू नको"], 25, "The speaker is encouraging secrecy from trusted adults."),
    "Platform migration": ([r"move.*(private|somewhere|app)", r"telegram", r"snap(chat)?", r"private.*chat", r"खाजगी"], 17, "The speaker is attempting to move the conversation to a more private channel."),
    "Image request": ([r"send.*(picture|photo|pic)", r"send me.*image", r"फोटो.*पाठव"], 27, "The speaker is requesting an image."),
    "Targeted insult": ([r"\b(ugly|loser|stupid|worthless)\b", r"बेकार", r"नालायक"], 16, "The message contains a targeted insult."),
    "Threat": ([r"\b(hurt|kill|expose) you\b", r"i'?ll.*ruin", r"मार"], 28, "The message contains threatening language."),
}


def detect_language(text: str) -> str:
    if re.search(r"[\u0900-\u097F]", text):
        if any(word in text for word in ("कुणाला", "आपण", "बोलतोय", "सांगू")):
            return "Marathi / Devanagari"
        return "Hindi / Devanagari"
    if re.search(r"\b(mat batana|baat karte|tum|hai)\b", text, re.I):
        return "Hinglish"
    return "English"


def analyze_message(message: str, conversation: list[str] | None = None) -> Analysis:
    """Score the new event only; history contributes through contextual combinations."""
    conversation = conversation or []
    normalized = message.lower()
    found: list[str] = []
    reasons: list[str] = []
    event_score = 0
    historical_signals: set[str] = set()
    for old in conversation:
        old_lower = old.lower()
        for name, (patterns, _, _) in SIGNALS.items():
            if any(re.search(pattern, old_lower, re.I) for pattern in patterns):
                historical_signals.add(name)
    for name, (patterns, weight, reason) in SIGNALS.items():
        if any(re.search(pattern, normalized, re.I) for pattern in patterns):
            found.append(name)
            event_score += weight
            reasons.append(reason)

    all_signals = historical_signals | set(found)
    # Context bonuses apply only when the new event advances a concerning pattern.
    bonus = 0
    if found and {"Age targeting", "Boundary testing", "Secrecy request"} & all_signals and len(all_signals) >= 3:
        bonus += 8
    if "Platform migration" in found and {"Age targeting", "Secrecy request"} <= all_signals:
        bonus += 7
    if "Image request" in found and {"Secrecy request", "Platform migration"} <= all_signals:
        bonus += 8
    if "Threat" in found and "Targeted insult" in all_signals:
        bonus += 8

    # Carry a constrained share of prior risk so scores escalate instead of resetting.
    prior = 0
    for old in conversation:
        for _, (patterns, weight, _) in SIGNALS.items():
            if any(re.search(pattern, old.lower(), re.I) for pattern in patterns):
                prior += weight
    score = min(100, event_score + bonus + min(45, round(prior * 0.55)))
    if not found:
        score = min(100, round(prior * 0.45))
    if score >= 75:
        level, action = "high", "Escalate for human review"
    elif score >= 40:
        level, action = "medium", "Warn and recommend review"
    else:
        level, action = "low", "Continue monitoring"
    if bonus:
        reasons.append("Multiple contextual indicators are occurring together, increasing concern.")
    explanation = " ".join(reasons) if reasons else "No strong behavioral risk signal was detected in this new message."
    return Analysis(score, level, detect_language(message), found, explanation, action)
