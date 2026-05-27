import os
import base64
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
import uvicorn
import json

from core.profile_manager import ProfileManager
from tools.document_parser import parse_resume
from agent.graph import app as agent_app

app = FastAPI(title="Autofill Agent API")

# Allow requests from the Chrome Extension and content scripts
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to your extension ID
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

profile_manager = ProfileManager()

# Where the uploaded resume file is stored on disk
RESUME_SAVE_PATH = os.path.join(os.path.dirname(__file__), "uploaded_resume.pdf")


class ProcessPageRequest(BaseModel):
    page_dom: str
    page_screenshot: str
    user_response: Optional[str] = None
    state_override: Optional[dict] = None


@app.post("/upload_resume")
async def upload_resume(file: UploadFile = File(...)):
    """
    1. Saves the raw file to disk (so we can serve it later to inject into file inputs).
    2. Parses the text content.
    3. Uses GPT-4o to extract structured profile data.
    4. Saves profile data + file metadata to profile.json.
    """
    contents = await file.read()

    # ── Step 1: persist the file so we can serve it for form file-upload fields ──
    with open(RESUME_SAVE_PATH, "wb") as f:
        f.write(contents)
    print(f"[upload_resume] Saved resume to {RESUME_SAVE_PATH}")

    # ── Step 2: extract raw text ──
    text = parse_resume(contents, file.filename)

    # ── Step 3: use LLM to extract structured profile ──
    from langchain_core.messages import HumanMessage
    from core.llm import get_llm

    llm = get_llm().bind(response_format={"type": "json_object"})
    prompt = f"""Extract the user's profile information from this resume text.
Include: full_name, email, phone, address, linkedin, github, website,
         work_experience (list), education (list), skills (list),
         and any other relevant fields.
Return a JSON object with a single key 'profile_data' containing all extracted fields.
Resume text:
{text}
"""
    response = llm.invoke([HumanMessage(content=prompt)])
    try:
        data = json.loads(response.content)
        profile_data = data.get("profile_data", {})

        # ── Step 4: also store file metadata so the agent knows a real file exists ──
        profile_data["_resume_file_saved"] = True
        profile_data["_resume_filename"] = file.filename

        profile_manager.update_profile(profile_data)
        print(f"[upload_resume] Profile updated with {len(profile_data)} fields.")
        return {"status": "success", "message": f"Resume parsed ✓  ({len(profile_data)} fields saved)"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.get("/get_resume")
async def get_resume():
    """
    Returns the saved resume file as a base64-encoded JSON payload.
    Called by content.js when it needs to programmatically set a file-upload input.
    """
    if not os.path.exists(RESUME_SAVE_PATH):
        return JSONResponse(status_code=404, content={"error": "No resume on file. Please upload one first."})

    profile = profile_manager.load_profile()
    filename = profile.get("_resume_filename", "resume.pdf")
    mime_type = "application/pdf" if filename.lower().endswith(".pdf") else "application/octet-stream"

    with open(RESUME_SAVE_PATH, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")

    return {"base64": b64, "filename": filename, "mime_type": mime_type}


@app.post("/process_page")
async def process_page(request: ProcessPageRequest):
    """
    Main agent entry point.
    The extension sends the page DOM + screenshot (and optionally a user answer).
    LangGraph runs to completion and returns either:
      - status="fill"  → list of browser actions (type / click / upload)
      - status="ask"   → a question string to show the user
    """
    initial_state = {
        "page_dom": request.page_dom,
        "page_screenshot": request.page_screenshot,
        "user_profile": profile_manager.load_profile(),
        "user_response": request.user_response,
        "form_fields": [],
        "mapped_data": [],
        "missing_fields": [],
        "actions_to_take": [],
        "status": "",
        "question_for_user": None,
    }

    # Reuse form_fields / missing_fields from a previous call to avoid re-parsing
    if request.state_override:
        initial_state.update(request.state_override)

    final_state = agent_app.invoke(initial_state)

    return {
        "status": final_state.get("status"),
        "actions": final_state.get("actions_to_take", []),
        "question": final_state.get("question_for_user"),
        # Returned so the extension can send it back on the next call
        "current_state": {
            "form_fields": final_state.get("form_fields"),
            "missing_fields": final_state.get("missing_fields"),
            "question_for_user": final_state.get("question_for_user"),
        },
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
