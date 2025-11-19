import os
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from database import db, create_document, get_documents
from schemas import Note, Flashcard, Question, Summary

app = FastAPI(title="Study Toolkit API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Study Toolkit Backend is running"}

# Notes Endpoints
@app.post("/api/notes")
def create_note(note: Note):
    try:
        inserted_id = create_document("note", note)
        return {"id": inserted_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/notes")
def list_notes(topic: Optional[str] = None):
    try:
        filter_dict = {"topic": topic} if topic else {}
        notes = get_documents("note", filter_dict)
        # convert ObjectId to str
        for n in notes:
            n["_id"] = str(n["_id"]) 
        return notes
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Flashcards Endpoints
@app.post("/api/flashcards")
def create_flashcard(card: Flashcard):
    try:
        inserted_id = create_document("flashcard", card)
        return {"id": inserted_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/flashcards")
def list_flashcards(tag: Optional[str] = None):
    try:
        filter_dict = {"tag": tag} if tag else {}
        cards = get_documents("flashcard", filter_dict)
        for c in cards:
            c["_id"] = str(c["_id"]) 
        return cards
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Tests/Questions Endpoints
@app.post("/api/questions")
def create_question(q: Question):
    try:
        inserted_id = create_document("question", q)
        return {"id": inserted_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/questions")
def list_questions(tag: Optional[str] = None):
    try:
        filter_dict = {"tag": tag} if tag else {}
        questions = get_documents("question", filter_dict)
        for q in questions:
            q["_id"] = str(q["_id"]) 
        return questions
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# File upload + summarization
class SummaryResponse(BaseModel):
    id: str
    summary: str

@app.post("/api/summarize", response_model=SummaryResponse)
async def summarize_file(file: UploadFile = File(...)):
    try:
        # Read the uploaded file's bytes
        content_bytes = await file.read()
        text = content_bytes.decode(errors="ignore")
        if not text or len(text.strip()) == 0:
            # For binary files (pdf, docx) we can't parse text here without extra deps.
            # Store a placeholder text so the record still persists.
            text = "(Binary file uploaded; text extraction not available in demo)"
        
        # Simple heuristic summary (first 3-5 sentences)
        summary = simple_summarize(text)
        
        # Persist in DB
        data = Summary(file_name=file.filename, text=text[:10000], summary=summary)
        inserted_id = create_document("summary", data)
        return {"id": inserted_id, "summary": summary}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/summaries")
def list_summaries(limit: int = 20):
    try:
        docs = get_documents("summary", {}, limit)
        for d in docs:
            d["_id"] = str(d["_id"]) 
        return docs
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def simple_summarize(text: str) -> str:
    # naive sentence split and take top few sentences
    sentences = [s.strip() for s in text.replace("\n", " ").split(".") if s.strip()]
    if not sentences:
        return "No content to summarize."
    selected = sentences[:5]
    return ". ".join(selected) + ("." if selected else "")


@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"
    
    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    return response


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
