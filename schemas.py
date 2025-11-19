"""
Database Schemas for Study App

Each Pydantic model defines a MongoDB collection (collection name is the lowercase class name).
"""

from pydantic import BaseModel, Field
from typing import List, Optional

class Note(BaseModel):
    title: str = Field(..., description="Note title")
    content: str = Field(..., description="Note content (markdown/plain text)")
    topic: Optional[str] = Field(None, description="Optional topic or tag")

class Flashcard(BaseModel):
    front: str = Field(..., description="Prompt/question")
    back: str = Field(..., description="Answer/definition")
    tag: Optional[str] = Field(None, description="Optional subject tag")

class Question(BaseModel):
    question: str = Field(..., description="Question text")
    options: List[str] = Field(..., min_items=2, description="Multiple-choice options")
    answer_index: int = Field(..., ge=0, description="Index of the correct option")
    tag: Optional[str] = Field(None, description="Optional subject tag")

class Summary(BaseModel):
    file_name: str = Field(..., description="Original uploaded file name")
    text: str = Field(..., description="Extracted raw text")
    summary: str = Field(..., description="Generated summary")
