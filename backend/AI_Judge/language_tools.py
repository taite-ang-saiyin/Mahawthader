import re

class LanguageDetector:
    """
    Tiny heuristic language detector; default to English.
    """

    def __init__(self, kb_path: str = "Project_KB_modified.json"):
        self.kb_path = kb_path

    def detect_language(self, text: str) -> str:
        if re.search(r'[\u1000-\u109F]', text):  # Burmese
            return "my"
        if re.search(r'[\u4E00-\u9FFF]', text):  # Chinese
            return "zh"
        if re.search(r'[\u3040-\u30FF]', text):  # Japanese
            return "ja"
        return "en"

    def get_language_name(self, lang_code: str) -> str:
        return {"en": "English", "my": "Burmese", "zh": "Chinese", "ja": "Japanese"}.get(lang_code, "English")
