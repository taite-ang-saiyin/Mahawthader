import json
from llm_handler import LLMHandler
import PyPDF2

class LegalAnalyzer:
    def __init__(self):
        self.llm_handler = LLMHandler()
        try:
            with open("laws.json", "r") as f:
                self.knowledge_base = json.load(f)
        except FileNotFoundError:
            self.knowledge_base = {
                "laws": [
                    {"id": "law1", "text": "Law 1: Contracts must be honored unless breached."},
                    {"id": "law2", "text": "Law 2: Property disputes require clear evidence of ownership."},
                    {"id": "law3", "text": "Law 3: Liability requires proof of negligence or intent."}
                ]
            }

    def get_relevant_laws(self, keywords=None):
        if not keywords:
            return self.knowledge_base["laws"]
        return [law for law in self.knowledge_base["laws"] if any(keyword.lower() in law["text"].lower() for keyword in keywords)]

    def extract_file_content(self, files):
        content = []
        for file in files:
            try:
                if hasattr(file, 'file'):
                    if file.filename.endswith(".pdf"):
                        pdf_reader = PyPDF2.PdfReader(file.file)
                        text = "".join(
                            page.extract_text() or "" for page in pdf_reader.pages
                        )
                        content.append(f"{file.filename}: {text}")
                    elif file.filename.endswith(".txt"):
                        text = file.file.read().decode('utf-8')
                        content.append(f"{file.filename}: {text}")
            except Exception as e:
                content.append(f"{file.filename}: [Error reading file: {str(e)}]")
        return content


    def analyze_scenario_and_files(self, scenario, plaintiff_files, defendant_files):
        plaintiff_content = self.extract_file_content(plaintiff_files)
        defendant_content = self.extract_file_content(defendant_files)
        context = f"Scenario: {scenario}\nPlaintiff Files: {', '.join(plaintiff_content)}\nDefendant Files: {', '.join(defendant_content)}"
        relevant_laws = self.get_relevant_laws([scenario] + [item for sublist in [plaintiff_content, defendant_content] for item in sublist])
        analysis = self.llm_handler.analyze_text(context, json.dumps(relevant_laws, indent=2))
        return analysis

    def analyze_message(self, message, role, initial_analysis):
        context = f"{role} statement: {message}\nInitial Analysis: {initial_analysis}"
        relevant_laws = self.get_relevant_laws([message])
        analysis = self.llm_handler.analyze_text(context, json.dumps(relevant_laws, indent=2))
        return analysis