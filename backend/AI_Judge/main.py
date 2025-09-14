from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from .case_flow import CaseFlow, LegalKnowledgeBase
import uvicorn
import re
from datetime import datetime
from typing import List, Optional
from .verdict_builder import _sanitize_filename
from fastapi import HTTPException

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

case_flow = CaseFlow()
HISTORY_DIR = "./history"

import pytz

MYANMAR_TZ = pytz.timezone("Asia/Yangon")
# -------------------------------
# Start new case
# -------------------------------
@app.post("/start_case")
async def start_case(
    case_title: str = Form(...),
    scenario: str = Form(...),
    plaintiff_name: str = Form(...),  # New field
    defendant_name: str = Form(...),  # New field
    plaintiff_files: List[UploadFile] = File(...),
    defendant_files: List[UploadFile] = File(...),
):
    # Enforce file count limits (1–3)
    if not (1 <= len(plaintiff_files) <= 3):
        return {"error": "Plaintiff must upload between 1 and 3 files."}
    if not (1 <= len(defendant_files) <= 3):
        return {"error": "Defendant must upload between 1 and 3 files."}

    print(f"Received plaintiff files: {[file.filename for file in plaintiff_files]}")
    print(f"Received defendant files: {[file.filename for file in defendant_files]}")

    case_id = case_flow.create_case(
        case_title, scenario, plaintiff_name, defendant_name, plaintiff_files, defendant_files
    )
    initial_analysis = await case_flow.analyze_initial(case_id)

    return {
        "case_id": case_id,
        "initial_analysis": initial_analysis,
        **case_flow.get_case_state(case_id),
        "language": case_flow.get_case_state(case_id).get("detected_lang")
    }


# -------------------------------
# Submit round messages
# -------------------------------
@app.post("/submit_message/{case_id}")
async def submit_message(
    case_id: str,
    message: str = Form(...),
    role: str = Form(...),
    files: Optional[List[UploadFile]] = File(None)   # ✅ optional
):
    # ✅ Enforce file count limits (1–3), if files are uploaded
    if files:
        if not (1 <= len(files) <= 3):
            return {"error": "You must upload between 1 and 3 files per round."}

    response_text = await case_flow.handle_message(case_id, message, role, files)

    return {
        "response": response_text,
        **case_flow.get_case_state(case_id),
        "language": case_flow.get_case_state(case_id).get("detected_lang")
    }


# -------------------------------
# Get verdict
# -------------------------------
from fastapi.responses import FileResponse
import os

"""
@app.get("/get_verdict/{case_id}")
async def get_verdict(case_id: str):
    verdict = await case_flow.get_final_verdict(case_id)
    case_data = case_flow.get_case_state(case_id)
    # Assume PDF was generated and stored in case_data["final_verdict_pdf"]
    pdf_path = case_flow.cases.get(case_id, {}).get("final_verdict_pdf", None)
    return {
        "verdict": verdict,
        "pdf_path": pdf_path if pdf_path and os.path.exists(pdf_path) else None,
        **case_data,
        "language": case_data.get("detected_lang")
    }
"""
@app.get("/get_verdict/{case_id}")
async def get_verdict(case_id: str):
    case_data = case_flow.cases.get(case_id, {})
    verdict = await case_flow.get_final_verdict(case_id)
    pdf_path = case_data.get("final_verdict_pdf", None)
    case_state = case_flow.get_case_state(case_id)

    if pdf_path and os.path.exists(pdf_path):
        return FileResponse(
            pdf_path,
            media_type="application/pdf",
            filename=f"verdict_{_sanitize_filename(case_data.get('case_title', 'case'))}_{case_id}.pdf",
            headers={"Content-Disposition": f"attachment; filename=verdict_{_sanitize_filename(case_data.get('case_title', 'case'))}_{case_id}.pdf"}
        )
    return {
        "error": "PDF not found",
        "verdict": verdict,
        **case_state,
        "language": case_state.get("detected_lang")
    }

@app.get("/download_verdict_pdf/{case_id}")
async def download_verdict_pdf(case_id: str):
    pdf_file = os.path.join(HISTORY_DIR, f"{case_id}.pdf")
    if os.path.exists(pdf_file):
        return FileResponse(
            pdf_file,
            media_type="application/pdf",
            filename=f"{case_id}.pdf"
        )
    raise HTTPException(status_code=404, detail="PDF not found")

@app.get("/get_case_state/{case_id}")
async def get_case_state(case_id: str):
    state = case_flow.get_case_state(case_id)
    if not state:
        return {"error": "Case not found"}
    case_data = case_flow.cases.get(case_id, {})
    return {
        **state,
        "final_verdict": case_data.get("final_verdict", ""),  # Include verdict text
        "language": case_data.get("detected_lang", "en")
    }

@app.get("/get_case_history")
async def get_case_history():
    try:
        if not os.path.exists(HISTORY_DIR):
            return []

        cases = []
        for file in os.listdir(HISTORY_DIR):
            if file.endswith(".pdf") and file.startswith("verdict_"):
                case_data = parse_case_file(file)
                if case_data:
                    cases.append(case_data)

        # sort newest first
        cases.sort(key=lambda c: c["verdict_date"], reverse=True)
        return cases
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch case history: {e}")

    
def parse_case_file(filename: str):
    """
    Extract case metadata from filename like:
    verdict_The_State_vs_The_Phoenix_Five_20250910_095446.pdf
    """
    match = re.match(r"verdict_(.+)_(\d{8}_\d{6})\.pdf", filename)
    if not match:
        return None
    
    case_title = match.group(1).replace("_", " ")
    verdict_date_str = match.group(2)
    verdict_date = datetime.strptime(verdict_date_str, "%Y%m%d_%H%M%S")
    verdict_date = MYANMAR_TZ.localize(verdict_date)
    
    return {
        "case_id": filename.replace(".pdf", ""),   # use filename as ID
        "case_title": case_title,
        "plaintiff_name": "",   # could extend parsing if needed
        "defendant_name": "",   # could extend parsing if needed
        "verdict_date": verdict_date.isoformat(),
        "pdf_path": os.path.join(HISTORY_DIR, filename)
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
