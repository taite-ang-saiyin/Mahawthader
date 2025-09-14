import uuid
import json
import os
from typing import Dict, List, Any, Optional
from fastapi import UploadFile
from .language_tools import LanguageDetector
from .llm_handler import LLMHandler
from .verdict_builder import VerdictBuilder
import PyPDF2
import re
from .rag import VectorIndexer
from datetime import datetime

# Resolve KB path relative to this module directory so it works from any CWD
KB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Project_KB_modified.json")

class LegalKnowledgeBase:
    """
    Loads a multi-language KB and provides vector-search (RAG) over sections.
    Expects JSON chapters with sections holding:
      - chapter_title_<lang>, title_<lang>, text_<lang>, and "section" id.
    """
    def __init__(self, kb_path: str):
        self.kb_path = kb_path
        self.kb = []
        try:
            with open(kb_path, "r", encoding="utf-8") as f:
                self.kb = json.load(f)
            print(f"Successfully loaded Knowledge Base from {kb_path}")
        except FileNotFoundError:
            print(f"Error: Knowledge Base file not found at {kb_path}")
        except json.JSONDecodeError:
            print(f"Error: Could not decode JSON from {kb_path}")

        # Build one cross-language index (stores lang in metadata)
        self.index = VectorIndexer(index_dir=".rag_cache", index_name="kb_sections")
        if not self.index.load():
            print("Building KB vector index (first run)...")
            texts, metas = self._flatten_kb()
            if texts:
                self.index.build(texts, metas)
                print("KB vector index built and cached.")
            else:
                print("KB appears empty; index not built.")

    def _flatten_kb(self):
        """
        Flatten chapters→sections into per-language “documents”.
        Each section produces a doc per language we find.
        """
        docs: List[str] = []
        metas: List[Dict] = []

        # Known language keys in your LanguageDetector
        lang_keys = ["en", "my", "zh", "ja"]

        for chapter in (self.kb or []):
            for section in chapter.get("sections", []):
                sec_id = section.get("section", "N/A")
                for lang in lang_keys:
                    chap_key = f"chapter_title_{lang}"
                    title_key = f"title_{lang}"
                    text_key  = f"text_{lang}"
                    chap = chapter.get(chap_key, "") or ""
                    title = section.get(title_key, "") or ""
                    text = section.get(text_key, "") or ""

                    if text.strip() or title.strip():
                        body = f"{chap}\nSection {sec_id}: {title}\n{text}".strip()
                        docs.append(body)
                        metas.append({
                            "lang": lang,
                            "section": sec_id,
                            "chapter_title": chap or "N/A",
                            "title": title or "N/A",
                            "text": text or "N/A",
                        })
        return docs, metas

    def find_relevant_laws(
        self,
        text_corpus: str,
        lang_code: str,
        top_k: int = 12,
        min_score: float = 0.25,
    ) -> List[Dict[str, str]]:
        """
        Vector-search the KB using the whole case text. Prefer matches in the detected language,
        but gracefully fall back to English if few results in that language.
        """
        if not self.kb:
            return []

        # 1) Search across all languages
        hits = self.index.search(text_corpus, top_k=top_k * 2)  # get more, filter below

        # 2) Prefer detected language; keep a small number of strong fallbacks
        primary, fallback = [], []
        for idx, score in hits:
            if score < min_score:
                continue
            meta = self.index.get_metadata(idx)
            record = {
                "chapter_title": meta.get("chapter_title", "N/A"),
                "section": meta.get("section", "N/A"),
                "title": meta.get("title", "N/A"),
                "text": meta.get("text", "N/A"),
                "score": score,
                "lang": meta.get("lang", "en"),
            }
            if record["lang"] == lang_code:
                primary.append(record)
            elif record["lang"] == "en":
                fallback.append(record)

        # 3) Merge, de-duplicate by section id, keep top_k
        primary.sort(key=lambda r: r["score"], reverse=True)
        fallback.sort(key=lambda r: r["score"], reverse=True)

        merged: List[Dict[str, str]] = []
        seen = set()
        for bucket in (primary, fallback):
            for r in bucket:
                sec = str(r["section"])
                if sec not in seen:
                    merged.append({k: r[k] for k in ["chapter_title","section","title","text"]})
                    seen.add(sec)
                if len(merged) >= top_k:
                    break
            if len(merged) >= top_k:
                break

        print(f"RAG: selected {len(merged)} law sections (lang={lang_code}, min_score={min_score}).")
        return merged

class CaseFlow:
    def __init__(self):
        self.cases: Dict[str, Dict[str, Any]] = {}
        self.language_detector = LanguageDetector(kb_path=KB_PATH)
        self.llm = LLMHandler()
        self.kb_handler = LegalKnowledgeBase(kb_path=KB_PATH)
        self.verdict_builder = VerdictBuilder()

    async def _call_llm(self, model_name: str, prompt: str) -> str:
        try:
            return await self.llm.generate_text(model_name, prompt)
        except Exception as e:
            print(f"LLM call failed: {e}")
            return "Error: Failed to get a response from AI Judge."

    def _extract_file_content(self, files: List[UploadFile]) -> Dict[str, str]:
        content = {}
        for file in files:
            try:
                file.file.seek(0)
                if file.filename.endswith(".pdf"):
                    pdf_reader = PyPDF2.PdfReader(file.file)
                    text = "".join(page.extract_text() or "" for page in pdf_reader.pages)
                    content[file.filename] = text
                elif file.filename.endswith(".txt"):
                    text = file.file.read().decode('utf-8')
                    content[file.filename] = text
            except Exception as e:
                content[file.filename] = f"[Error reading file: {str(e)}]"
        return content

    def create_case(
        self,
        case_title: str,
        scenario: str,
        plaintiff_name: str,  # New parameter
        defendant_name: str,  # New parameter
        plaintiff_files: List[UploadFile],
        defendant_files: List[UploadFile]
    ) -> str:
        case_id = str(uuid.uuid4())
        plaintiff_content = self._extract_file_content(plaintiff_files)
        defendant_content = self._extract_file_content(defendant_files)

        self.cases[case_id] = {
            "case_title": case_title,
            "scenario": scenario,
            "plaintiff_name": plaintiff_name,  # Store plaintiff name
            "defendant_name": defendant_name,  # Store defendant name
            "initial_plaintiff_files": plaintiff_content,
            "initial_defendant_files": defendant_content,
            "plaintiff_round_files": {},
            "defendant_round_files": {},
            "round_statements": {},
            "chat_history": [],
            "current_round": 0,
            "current_speaker": "judge",
            "status": "initial_analysis",
            "final_verdict": None,
            "detected_lang": None,
        }
        print(f"Case {case_id} created with file content extracted.")
        return case_id

    async def analyze_initial(self, case_id: str) -> str:
        case_data = self.cases.get(case_id)
        if not case_data:
            return "Error: Case not found."
        lang_code = self.language_detector.detect_language(case_data["scenario"])
        case_data["detected_lang"] = lang_code
        response_language = self.language_detector.get_language_name(lang_code)
        case_data["current_round"] = 1
        prompt = f"""
        Hello! I'm an AI Judge presiding over a legal case. Respond entirely in {response_language}.
        Case title: "{case_data['case_title']}"

        Welcome, parties. This tribunal will proceed in 3 rounds.
        Each round will allow the Plaintiff and Defendant to submit statements in turn, optionally uploading supporting files.

        This is **Round 1**, and it is now the **Plaintiff's turn** to submit their statement.
        """

        judge_opening = await self._call_llm("gemini-1.5-flash-latest", prompt)
        case_data["chat_history"].append({"sender": "judge", "text": judge_opening})
        case_data["current_speaker"] = "plaintiff"
        case_data["status"] = "in_progress"
        return judge_opening

    async def handle_message(self, case_id: str, message: str, role: str, files: Optional[List[UploadFile]] = None) -> str:
        case_data = self.cases.get(case_id)
        if not case_data:
            return "Error: Case not found."

        if isinstance(message, bytes):
            message = message.decode('utf-8', errors='replace')

        if case_data["status"] != "in_progress":
            return "The court is not in session."
        if case_data["current_speaker"] != role:
            return f"It is currently the {case_data['current_speaker']}'s turn."

        # Save chat log
        case_data["chat_history"].append({"sender": role, "text": message})

        # Save per-round statement
        rnd = case_data["current_round"]
        next_rnd = case_data["current_round"] + 1
        case_data["round_statements"].setdefault(rnd, {"Plaintiff": "", "Defendant": ""})
        case_data["round_statements"][rnd][role] = message

        # Save per-round files
        if files:
            file_content = self._extract_file_content(files)
            round_key = f"round_{rnd}"
            if role == "plaintiff":
                case_data["plaintiff_round_files"][round_key] = file_content
            else:
                case_data["defendant_round_files"][round_key] = file_content

        # Turn-taking logic
        if role == "plaintiff":
            next_speaker = "defendant"
            judge_prompt = f"""
            The Plaintiff has submitted their statement for Round {rnd}.
                Round {rnd} for the Plaintiff is now complete.
                It is now the **Defendant's turn** to submit their statement for Round {rnd}.

                """

            judge_response = await self._call_llm("gemini-1.5-flash-latest", judge_prompt)

        else:  # defendant
            if case_data["current_round"] < 3:
                current_round_number = case_data['current_round']
                case_data['current_round'] += 1
                next_speaker = "plaintiff"
                judge_prompt = f"""
                The Defendant has submitted their statement for Round {rnd}.
                Round {rnd} for the Defendant is now complete.
                It is now the **Plaintiff's turn** to submit their statement for Round {next_rnd}.

                """

                judge_response = await self._call_llm("gemini-1.5-flash-latest", judge_prompt)
            else:  # defendant in final round
                case_data["status"] = "awaiting_verdict"
                final_verdict = await self.get_final_verdict(case_id)
                case_data["status"] = "verdict_rendered"
                case_data["final_verdict_message"] = final_verdict  # store separately

                next_speaker = None  # no one can speak now

                # Judge announcement for chat (optional, short)
                judge_response = (
                    f"Round 3 of Defendant is finished.\n"
                    f"The court session is now concluded. The final verdict has been issued in the Verdict section."
                )


        case_data["current_speaker"] = next_speaker
        case_data["chat_history"].append({"sender": "judge", "text": judge_response})
        return judge_response

    async def get_final_verdict(self, case_id: str) -> str:
        case_data = self.cases.get(case_id)
        if not case_data:
            return "Error: Case not found."
        if case_data["final_verdict"]:
            return case_data["final_verdict"]

        lang_code = case_data.get("detected_lang", "en")

        chat_texts = '\n'.join([f"{msg['sender']}: {msg['text']}" for msg in case_data['chat_history']])
        initial_plaintiff_files = '\n'.join(case_data.get('initial_plaintiff_files', {}).values())
        initial_defendant_files = '\n'.join(case_data.get('initial_defendant_files', {}).values())

        plaintiff_round_files_text = ""
        for round_num, files in case_data.get("plaintiff_round_files", {}).items():
            plaintiff_round_files_text += f"\n--- Plaintiff Files for {round_num} ---\n"
            plaintiff_round_files_text += "\n".join(files.values())

        defendant_round_files_text = ""
        for round_num, files in case_data.get("defendant_round_files", {}).items():
            defendant_round_files_text += f"\n--- Defendant Files for {round_num} ---\n"
            defendant_round_files_text += "\n".join(files.values())

        full_text_corpus = (
            f"{case_data['case_title']}\n{case_data['scenario']}\n{chat_texts}\n"
            f"{initial_plaintiff_files}\n{initial_defendant_files}\n"
            f"{plaintiff_round_files_text}\n{defendant_round_files_text}"
        )

        relevant_laws = self.kb_handler.find_relevant_laws(full_text_corpus, lang_code)

        rounds_struct = {}
        for i in sorted(case_data.get("round_statements", {}).keys()):
            rd = case_data["round_statements"][i]
            rounds_struct[i] = {
                "plaintiff": rd.get("plaintiff", "No statement"),
                "defendant": rd.get("defendant", "No statement"),
            }

        structured_case = {
            "title": case_data["case_title"],
            "scenario": case_data["scenario"],
            "plaintiff_name": case_data["plaintiff_name"],  # Pass plaintiff name
            "defendant_name": case_data["defendant_name"],  # Pass defendant name
            "plaintiff_files": list(case_data.get("initial_plaintiff_files", {}).keys()),
            "defendant_files": list(case_data.get("initial_defendant_files", {}).keys()),
            "rounds": rounds_struct
        }
        print(">>> VerdictBuilder received case:", structured_case)
        final_verdict, plaintiff_name, defendant_name, pdf_path = await self.verdict_builder.build_verdict(structured_case)
        case_data["final_verdict"] = final_verdict
        case_data["final_verdict_pdf"] = pdf_path
        case_data["verdict_date"] = datetime.now().isoformat()
        return final_verdict

    def get_case_state(self, case_id: str) -> dict:
        case_data = self.cases.get(case_id, {})
        return {
            "current_speaker": case_data.get("current_speaker"),
            "current_round": case_data.get("current_round"),
            "status": case_data.get("status"),
            "detected_lang": case_data.get("detected_lang"),
        }
