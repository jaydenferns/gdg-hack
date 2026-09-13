"""Provider boundary: replace LocalAIProvider with an LLM/NLP implementation later."""
from risk_engine import Analysis, analyze_message


class LocalAIProvider:
    def analyze(self, message: str, conversation: list[str]) -> Analysis:
        return analyze_message(message, conversation)


provider = LocalAIProvider()
