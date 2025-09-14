import json
import os
import re
from typing import List, Dict, Tuple, Any
from .llm_handler import LLMHandler
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from datetime import datetime
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY, TA_RIGHT
from .rag import VectorIndexer

WORD = r"\b{}\b"

def wre(word: str) -> re.Pattern:
    """Compile a case-insensitive regex pattern for a word boundary match."""
    return re.compile(WORD.format(re.escape(word)), flags=re.IGNORECASE)

def count_matches(text: str, patterns: List[re.Pattern]) -> int:
    """Count how many regex patterns match the text at least once."""
    return sum(1 for p in patterns if p.search(text))

def _sanitize_filename(name: str) -> str:
    """Sanitize a string to be safe for use as a filename."""
    sanitized = re.sub(r'[^\w\s-]', '', name).strip()
    sanitized = re.sub(r'\s+', '_', sanitized)
    return sanitized[:50]

class VerdictBuilder:
    """AI Tribunal Verdict Builder with Professional Court Design"""

    def __init__(self, kb_file: str = "Project_KB_modified.json"):
        # Resolve KB relative to this module (backend/AI_Judge)
        base_dir = os.path.dirname(os.path.abspath(__file__))
        kb_path = os.path.join(base_dir, kb_file)
        if not os.path.exists(kb_path):
            raise FileNotFoundError(f"Knowledge Base file not found at {kb_path}")
        with open(kb_path, "r", encoding="utf-8") as f:
            self.kb = json.load(f)

        self.laws: Dict[str, Dict[str, Any]] = {}
        texts, metadata = [], []
        for chapter in self.kb:
            for section in chapter.get("sections", []):
                sec_id = str(section["section"])
                self.laws[sec_id] = section
                texts.append(f"{section.get('title_en','')}. {section.get('text_en','')}".strip())
                metadata.append({
                    "section": sec_id,
                    "title_en": section.get("title_en", ""),
                    "text_en": section.get("text_en", ""),
                })

        # ✅ Initialize vector indexer
        self.indexer = VectorIndexer(index_name="kb_index")
        if not self.indexer.load():
            self.indexer.build(texts, metadata)

        self.llm = LLMHandler()

        self.colors = {
            'court_navy': colors.HexColor("#1e293b"),
            'court_navy_light': colors.HexColor("#334155"),
            'court_gold': colors.HexColor("#3B5169"),
            'document_bg': colors.HexColor("#fefefe"),
            'document_border': colors.HexColor("#e2e8f0"),
            'document_text': colors.HexColor("#1e293b"),
            'document_muted': colors.HexColor("#A3B5C7"),
            'section_bg': colors.HexColor("#f8fafc"),
        }

        # Domain keywords (still used for classification)
        self.domain_kw = {
            "penal": [
                wre("murder"), wre("homicide"), wre("killed"), wre("stabbed"),
                wre("death"), wre("robbery"), wre("dacoity"), wre("theft"),
                wre("assault"), wre("burglary"), wre("trespass"),
                wre("food"), wre("drink"), wre("noxious"), wre("poison"), 
                wre("contaminated"), wre("unfit for consumption"), wre("health"), wre("inspection"),
            ],
            "telecom": [
                wre("call log"), wre("phone record"), wre("telecom"), wre("subscriber"),
            ],
            "cybersecurity": [
                wre("hack"), wre("malware"), wre("phishing"), wre("unauthorized access"),
                wre("cyber"), wre("internet"), wre("digital"),
                wre("photo"), wre("image"), wre("defame"), wre("dishonest"),
            ],
            "military": [
                wre("soldier"), wre("army"), wre("desertion"), wre("mutiny"),
                wre("insubordination"), wre("military service"), wre("evade"),
                wre("doctor"), wre("medical note"), wre("false illness"),
                wre("fake certificate"), wre("alibi"), wre("disability"),
            ],
        }

        # Defense & evidence patterns
        self.defense_patterns = [
            wre("self[- ]defen[cs]e"), wre("under duress"), wre("coercion"),
            wre("necessity"), wre("insanity"), wre("alibi"),
            wre("consent(ed)?"), wre("provocation"),
        ]
        self.evidence_patterns = [
            wre("confession"), wre("fingerprint"), wre("footprint"),
            wre("fiber"), wre("recovered"), wre("witness"),
            wre("video"), wre("surveillance"),
        ]

        self._register_fonts()

    def _register_fonts(self):
        """Register available fonts from a package-local `fonts` directory when present.
        Falls back silently to system defaults if files are missing."""
        font_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")

        try:
            # Arial regular → also map as Helvetica if available for consistency
            arial_path = os.path.join(font_dir, "Arial.ttf")
            if os.path.exists(arial_path):
                pdfmetrics.registerFont(TTFont("Arial", arial_path))
                pdfmetrics.registerFont(TTFont("Helvetica", arial_path))

            # Arial bold → also map to Helvetica-Bold if present
            arial_bold_path = os.path.join(font_dir, "Arial-Bold.ttf")
            if os.path.exists(arial_bold_path):
                pdfmetrics.registerFont(TTFont("Arial-Bold", arial_bold_path))
                pdfmetrics.registerFont(TTFont("Helvetica-Bold", arial_bold_path))

            # Emoji / DejaVu fonts – try local, then silently ignore if unavailable
            noto_emoji_path = os.path.join(font_dir, "NotoEmoji-VariableFont_wght.ttf")
            if os.path.exists(noto_emoji_path):
                pdfmetrics.registerFont(TTFont("NotoEmoji", noto_emoji_path))
            else:
                try:
                    pdfmetrics.registerFont(TTFont("NotoEmoji", "NotoEmoji-VariableFont_wght.ttf"))
                except Exception:
                    pass

            dejavu_path = os.path.join(font_dir, "DejaVuSans.ttf")
            if os.path.exists(dejavu_path):
                pdfmetrics.registerFont(TTFont("DejaVuSans", dejavu_path))
            else:
                try:
                    pdfmetrics.registerFont(TTFont("DejaVuSans", "DejaVuSans.ttf"))
                except Exception:
                    pass

            # Optional italic
            arial_italic_path = os.path.join(font_dir, "Arial-Italic.ttf")
            if os.path.exists(arial_italic_path):
                pdfmetrics.registerFont(TTFont("ArialItalic", arial_italic_path))

        except Exception as e:
            print(f"Error registering custom fonts: {e}")
            print("Using default system fonts.")

    async def build_verdict(self, case: Dict[str, Any], output_dir: str = "./history", lang_code: str = "en") -> tuple[str, str, str, str]:
        """
        Build verdict and automatically generate a PDF.
        Returns (verdict_text, plaintiff_name, defendant_name, pdf_path).
        """
        title = case.get("title", "Unknown Case")
        scenario = case.get("scenario", "")
        rounds = case.get("rounds", {})
        plaintiff_name = case.get("plaintiff_name", "Unknown")
        defendant_name = case.get("defendant_name", "Unknown")

        plaintiff_text = " ".join(r.get("plaintiff", "") for r in rounds.values())
        defendant_text = " ".join(r.get("defendant", "") for r in rounds.values())
        all_text = title + " " + scenario + " " + plaintiff_text + " " + defendant_text

        domain = self._classify_domain(all_text.lower())
        applicable = self._discover_applicable(domain, scenario)
        if not applicable:
            reasoning = await self.llm.analyze_text(scenario, "No applicable laws found.")
            verdict = self._format_verdict(title, scenario, [], reasoning, "Defendant acquitted.", 0, plaintiff_name, defendant_name)
            case_id = _sanitize_filename(title) + "_" + datetime.now().strftime("%Y%m%d_%H%M%S")
            pdf_path = await self.generate_verdict_pdf(verdict, case_id, title, output_dir, lang_code, plaintiff_name, defendant_name)
            return (verdict, plaintiff_name, defendant_name, pdf_path)

        evidence_score = self._score_evidence(all_text)
        has_defense = any(p.search(defendant_text) for p in self.defense_patterns)
        if has_defense and evidence_score < 5:
            reasoning = await self.llm.analyze_text(
                scenario,
                "\n".join([label for (label, _) in applicable]) + "\nDefense: raised"
            )
            verdict = self._format_verdict(title, scenario, applicable, reasoning, "Defendant acquitted.", 0, plaintiff_name, defendant_name)
            case_id = _sanitize_filename(title) + "_" + datetime.now().strftime("%Y%m%d_%H%M%S")
            pdf_path = await self.generate_verdict_pdf(verdict, case_id, title, output_dir, lang_code, plaintiff_name, defendant_name)
            return (verdict, plaintiff_name, defendant_name, pdf_path)

        total_years = 0
        decisions = []
        for label, law_info in applicable:
            sentence = self._choose_sentence(law_info, scenario, evidence_score)
            years = self._extract_years(sentence)
            total_years += years
            decisions.append(f"Guilty under {label}: {sentence}")

        reasoning = await self.llm.analyze_text(
            scenario,
            "\n".join([label for (label, _) in applicable]) + f"\nEvidence score: {evidence_score}"
        )

        verdict = self._format_verdict(title, scenario, applicable, reasoning, "\n".join(decisions), total_years, plaintiff_name, defendant_name)
        case_id = _sanitize_filename(title) + "_" + datetime.now().strftime("%Y%m%d_%H%M%S")
        pdf_path = await self.generate_verdict_pdf(verdict, case_id, title, output_dir, lang_code, plaintiff_name, defendant_name)
        return (verdict, plaintiff_name, defendant_name, pdf_path)

    async def generate_verdict_pdf(
        self,
        verdict_text: str,
        case_id: str,
        case_title: str,
        output_dir: str = "./history",
        lang_code: str = "en",
        plaintiff_name: str = "Unknown",
        defendant_name: str = "Unknown"
    ) -> str:
        """Generate a professionally styled PDF matching the elegant court design"""
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_title = _sanitize_filename(case_title)
        pdf_filename = f"verdict_{safe_title}_{timestamp}.pdf"
        pdf_path = os.path.join(output_dir, pdf_filename)

        doc = SimpleDocTemplate(
            pdf_path,
            pagesize=letter,
            topMargin=0.5 * inch,
            bottomMargin=1 * inch,
            leftMargin=0.5 * inch,
            rightMargin=0.5 * inch
        )

        styles = self._create_elegant_styles(lang_code)
        elements = []

        elements.extend(self._create_elegant_court_header(case_id, styles))
        elements.append(Spacer(1, 0.5 * inch))

        elements.extend(self._create_elegant_case_header(verdict_text, case_id, styles, plaintiff_name, defendant_name))
        elements.append(Spacer(1, 0.3 * inch))

        sections = self._parse_verdict_sections(verdict_text)
        for section_title, content in sections.items():
            if content.strip():
                section_elements = self._create_elegant_section(section_title, content, styles)
                # Do NOT force KeepTogether for long sections (allows automatic page breaks)
                elements.append(KeepTogether(section_elements)) 
                #elements.extend(section_elements)

        def add_elegant_footer(canvas, doc):
            canvas.saveState()
            canvas.setStrokeColor(self.colors['court_gold'])
            canvas.setLineWidth(3)
            canvas.line(0.75 * inch, 0.75 * inch, doc.pagesize[0] - 0.75 * inch, 0.75 * inch)
            canvas.setFillColor(self.colors['document_muted'])
            canvas.setFont("Helvetica", 9)
            date_str = datetime.now().strftime('%B %d, %Y at %I:%M %p')
            canvas.drawString(0.75 * inch, 0.5 * inch, f"{date_str}")
            canvas.drawRightString(doc.pagesize[0] - 0.75 * inch, 0.5 * inch, f"Page {canvas.getPageNumber()}")
            canvas.setFont("DejaVuSans", 8)
            canvas.drawCentredString(doc.pagesize[0] / 2, 0.3 * inch, "⚖️ OFFICIAL COURT DOCUMENT ⚖️")
            canvas.restoreState()

        try:
            doc.build(elements, onFirstPage=add_elegant_footer, onLaterPages=add_elegant_footer)
        except Exception as e:
            print(f"Error generating elegant PDF: {e}")
            raise
        return pdf_path

    def _create_elegant_styles(self, lang_code: str):
        """Create elegant styles matching the sophisticated court design"""
        styles = getSampleStyleSheet()
        
        font_map = {
            "en": "Arial",
            "my": "Arial",
            "zh": "Arial",
            "ja": "Arial"
        }
        body_font = font_map.get(lang_code, "Helvetica")

        styles.add(ParagraphStyle(
            name='ElegantCourtTitle',
            fontName='Helvetica-Bold',
            fontSize=22,
            textColor=self.colors['court_navy'],
            spaceAfter=15,
            alignment=TA_CENTER,
            leading=32,
            spaceBefore=30
        ))

        styles.add(ParagraphStyle(
            name='ElegantCourtSubtitle',
            fontName='Helvetica',
            fontSize=12,
            textColor=self.colors['court_navy_light'],
            spaceBefore=10,
            spaceAfter=10,
            alignment=TA_CENTER,
            leading=20,
        ))

        styles.add(ParagraphStyle(
            name='ElegantJudgeName',
            fontName='Helvetica-Bold',
            fontSize=14,
            textColor=self.colors['court_navy'],
            spaceAfter=2,
            alignment=TA_CENTER,
            leading=18
        ))

        styles.add(ParagraphStyle(
            name='ElegantSectionTitle',
            fontName='NotoEmoji',
            fontSize=12,
            textColor=self.colors['court_navy'],
            spaceAfter=0,
            alignment=TA_LEFT,
            leading=20,
            spaceBefore=0
        ))

        styles.add(ParagraphStyle(
            name='ElegantBodyText',
            fontName=body_font,
            fontSize=10.5,
            textColor=self.colors['document_text'],
            spaceAfter=12,
            leading=18,
            alignment=TA_JUSTIFY,
            leftIndent=20,
            bulletIndent=10,
        ))

        styles.add(ParagraphStyle(
            name='ElegantCaseInfo',
            fontName='Helvetica',
            fontSize=11,
            textColor=self.colors['document_text'],
            spaceAfter=4,
            leading=14,
            alignment=TA_LEFT
        ))

        styles.add(ParagraphStyle(
            name="ElegantCourtSeal",
            fontName="NotoEmoji",
            fontSize=30,
            textColor=self.colors['court_gold'],
            alignment=TA_CENTER,
            spaceAfter=30,
        ))

        styles.add(ParagraphStyle(
            name="ElegantCourtJudge",
            fontName="Helvetica",
            fontSize=11,
            textColor=self.colors['court_navy'],
            alignment=TA_CENTER,
            spaceAfter=15,
        ))

        styles.add(ParagraphStyle(
            name='CaseHeaderPrimary',
            fontName='Helvetica-Bold',
            fontSize=13,
            leading=16,
            textColor=self.colors['document_text'],
            alignment=TA_LEFT,
            spaceAfter=15,
        ))

        styles.add(ParagraphStyle(
            name='CaseHeaderSecondary',
            fontName='Helvetica-Bold',
            fontSize=12,
            leading=16,
            textColor=self.colors['document_text'],
            alignment=TA_LEFT,
            spaceAfter=15,
        ))

        styles.add(ParagraphStyle(
            name='CaseHeaderTertiary',
            fontName='Helvetica',
            fontSize=11,
            leading=16,
            textColor=self.colors['document_text'],
            alignment=TA_LEFT,
            spaceAfter=15,
        ))

        styles.add(ParagraphStyle(
            name='CaseHeaderSmall',
            fontName='ArialItalic',
            fontSize=10,
            leading=16,
            textColor=self.colors['document_muted'],
            alignment=TA_LEFT,
            spaceAfter=15,
        ))

        return styles

    def _create_elegant_court_header(self, case_id: str, styles):
        """Create elegant court header with emoji + text support"""
        elements = []
        
        row_heights = [0.8 * inch, 0.8 * inch, 0.4 * inch, 0.4 * inch, 0.4 * inch]
        
        header_data = [
            [Paragraph('<font name="NotoEmoji">⚖️</font>', styles['ElegantCourtSeal'])],
            [Paragraph('<font name="Helvetica-Bold">MAHAWTHADER AI JUSTICE</font>', styles['ElegantCourtTitle'])],
            [Paragraph("", styles['ElegantCourtSubtitle'])],
            [Paragraph('<font name="Helvetica">SUPREME COURT OF JUSTICE</font>', styles['ElegantCourtJudge'])],
            [Paragraph('<font name="Helvetica">PRESIDING</font>', styles['ElegantCourtJudge'])],
        ]
        
        table = Table(header_data, rowHeights=row_heights)
        table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BACKGROUND', (0, 0), (-1, -1), self.colors['document_bg']),
            ('LINEBELOW', (0, 1), (-1, 1), 2, self.colors['document_muted']),
            ('LINEBELOW', (0, 4), (-1, 4), 2, self.colors['court_gold']),
            ('TOPPADDING', (0, 0), (0, 0), 30),
            ('BOTTOMPADDING', (0, 0), (0, 0), 30),
            ('TOPPADDING', (0, 1), (0, 1), 30),
            ('BOTTOMPADDING', (0, 1), (0, 1), 30),
            ('TOPPADDING', (0, 3), (0, 3), 10),
            ('BOTTOMPADDING', (0, 3), (0, 3), 15),
            ('TOPPADDING', (0, 4), (0, 4), 15),
            ('BOTTOMPADDING', (0, 4), (0, 4), 20),
        ]))
        
        elements.append(table)
        return elements

    def _create_elegant_case_header(self, verdict_text: str, case_id: str, styles, plaintiff_name: str, defendant_name: str):
        """Create elegant case information header"""
        elements = []

        case_info_data = [
            [Paragraph(plaintiff_name, styles['CaseHeaderPrimary']), 
             Paragraph(f"Case No. {case_id[-8:]}", styles['CaseHeaderSecondary'])],
            [Paragraph("Plaintiff", styles['CaseHeaderSmall']), 
             Paragraph(f"Filed: {datetime.now().strftime('%B %d, %Y')}", styles['CaseHeaderTertiary'])],
            [Paragraph("", styles['CaseHeaderTertiary']), 
             Paragraph("", styles['CaseHeaderTertiary'])],
            [Paragraph("v.", styles['CaseHeaderPrimary']), 
             Paragraph("", styles['CaseHeaderTertiary'])],
            [Paragraph("", styles['CaseHeaderTertiary']), 
             Paragraph("", styles['CaseHeaderTertiary'])],
            [Paragraph(defendant_name, styles['CaseHeaderPrimary']), 
             Paragraph(f"Document #{case_id[-4:]}", styles['CaseHeaderTertiary'])],
            [Paragraph("Defendant", styles['CaseHeaderSmall']), 
             Paragraph(f"Verdict Date: {datetime.now().strftime('%B %d, %Y')}", styles['CaseHeaderTertiary'])]
        ]

        table = Table(case_info_data, colWidths=[3.5 * inch, 3.5 * inch], 
                      rowHeights=[0.4 * inch, 0.4 * inch, 0.25 * inch, 0.25 * inch, 0.25 * inch, 0.4 * inch, 0.4 * inch])
        table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BACKGROUND', (0, 0), (-1, -1), colors.white),
            ('TOPPADDING', (0, 0), (-1, -1), 15),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
            ('LEFTPADDING', (0, 0), (-1, -1), 12),
            ('RIGHTPADDING', (0, 0), (0, -1), 12),
            ('RIGHTPADDING', (1, 0), (1, -1), 8),
            ('BOTTOMPADDING', (1, 0), (1, 0), 15),
            ('TOPPADDING', (1, 1), (1, 1), 15),
        ]))
        
        elements.append(table)
        return elements

    def _create_elegant_section(self, title: str, content: str, styles):
        """
        Create a flowing section (header + paragraphs) that avoids LayoutError.
        - title: section title (e.g. "SCENARIO", "COURT'S REASONING")
        - content: full text for that section (string)
        Returns a list of flowables (Paragraphs/Spacers).
        """
        elements = []

        # icons per section
        section_icons = {
            "CASE TITLE": "📋",
            "SCENARIO": "📝",
            "APPLICABLE LAW": "⚖️",
            "COURT'S REASONING": "🏛️",
            "DECISION": "✅",
            "TOTAL IMPRISONMENT": "⏰",
            "SENTENCE": "⏰"
        }
        icon = section_icons.get(title.upper(), "📄")

        # header (emoji + bold title)
        header_text = (
            f'<font name="NotoEmoji">{icon}</font> '
            f'<font name="Helvetica-Bold">{title}</font>'
        )
        elements.append(Paragraph(header_text, styles['ElegantSectionTitle']))
        elements.append(Spacer(1, 0.12 * inch))

        # split content into lines then into bullet-like items
        content_lines = [ln.strip() for ln in content.split("\n") if ln.strip()]
        all_items = []
        for line in content_lines:
            # split on bullets or hyphens, but if none found keep whole line
            items = [itm.strip() for itm in re.split(r'\s*[-•]\s+', line) if itm.strip()]
            if not items:
                items = [line]
            all_items.extend(items)

        # create paragraphs for each item (allow natural page breaks)
        for item in all_items:
            if title.upper() == "APPLICABLE LAW":
                # show a bullet symbol — keep it simple and flowing
                text = f'• {item}'
                elements.append(Paragraph(text, styles['ElegantBodyText']))
            else:
                elements.append(Paragraph(item, styles['ElegantBodyText']))
            elements.append(Spacer(1, 0.08 * inch))

        # small gap after section
        elements.append(Spacer(1, 0.20 * inch))
        return elements


    def _parse_verdict_sections(self, verdict_text: str) -> Dict[str, str]:
        """Parse verdict text into structured sections"""
        sections = {
            "CASE TITLE": "",
            "SCENARIO": "",
            "APPLICABLE LAW": "",
            "COURT'S REASONING": "",
            "DECISION": "",
            "TOTAL IMPRISONMENT": "",
            "SENTENCE": ""
        }
        
        current_section = None
        for line in verdict_text.split("\n"):
            line = line.strip()
            if line.endswith(":") and line[:-1] in sections:
                current_section = line[:-1]
            elif current_section and line:
                sections[current_section] += line + " "
        
        return sections

    def _classify_domain(self, text: str) -> str:
        scores = {d: count_matches(text, pats) for d, pats in self.domain_kw.items()}
        return max(scores.items(), key=lambda kv: kv[1])[0] if any(scores.values()) else "penal"

    def _discover_applicable(self, domain: str, scenario: str) -> List[Tuple[str, Dict[str, Any]]]:
        results = self.indexer.search(scenario, top_k=3)
        matched = []
        for idx, score in results:
            meta = self.indexer.get_metadata(idx)
            matched.append((self._law_label(meta, meta["section"]), meta))
        return matched

    def _score_evidence(self, text: str) -> int:
        return sum(count_matches(text, [p]) for p in self.evidence_patterns)

    def _choose_sentence(self, law_info: Dict[str, Any], scenario: str, evidence_score: int) -> str:
        statute = (law_info.get("text_en") or "").lower()
        allows_life = "life imprisonment" in statute
        allows_death = "death" in statute

        years_match = [int(x) for x in re.findall(r"(\d+)\s*year", statute)]
        min_year = min(years_match) if years_match else 1
        max_year = max(years_match) if years_match else 10

        severity = evidence_score
        if allows_death and severity >= 5:
            return "life imprisonment."
        if allows_life:
            return "life imprisonment."
        term = min_year + (max_year - min_year) * min(severity, 5) // 5
        return f"{term} years' imprisonment."

    def _extract_years(self, sentence: str) -> int:
        match = re.search(r"(\d+)\s*year", sentence)
        return int(match.group(1)) if match else 0

    def _law_label(self, law: Dict[str, Any], section: str) -> str:
        title = law.get("title_en") or f"Section {section}"
        return f"{title} (Section {section})"

    def _format_verdict(
        self,
        case_title: str,
        scenario: str,
        laws: List[Tuple[str, Dict[str, Any]]],
        reasoning: str,
        decision_text: str,
        total_years: int,
        plaintiff_name: str,
        defendant_name: str
    ) -> str:
        law_list = "\n".join(f"- {label}" for (label, _law) in laws) if laws else "None"
        verdict = (
            "FINAL JUDGMENT AND ORDER:\n\n"
            f"CASE TITLE:\n{case_title}\n\n"
            f"SCENARIO:\n{scenario}\n\n"
            f"APPLICABLE LAW:\n{law_list}\n\n"
            f"COURT'S REASONING:\n{reasoning}\n\n"
            f"DECISION:\n{decision_text}\n"
        )
        if "life imprisonment" in decision_text.lower():
            verdict += "SENTENCE:\nLife Imprisonment!\n"
        elif total_years:
            verdict += f"TOTAL IMPRISONMENT:\n{total_years} years\n"
        return verdict