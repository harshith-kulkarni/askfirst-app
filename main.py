"""
FastAPI backend for the AI Chat App.

Run with:
    uvicorn main:app --reload --port 8000
"""

import os
from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from dotenv import load_dotenv

from database import (
    init_db, get_db,
    create_thread, get_threads, get_thread, delete_thread,
    get_messages, add_message,
    get_universal_memory, add_universal_memory,
)

load_dotenv()

app = FastAPI(title="AI Chat API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Startup ──────────────────────────────────────────────────────────────────

@app.on_event("startup")
def startup():
    init_db()


# ─── LLM Client Factory ───────────────────────────────────────────────────────

def get_llm_client():
    """
    Returns a callable: stream(messages) -> generator of text chunks.

    Provider is selected via LLM_PROVIDER env var:
      'openrouter' (default) | 'openai' | 'groq' | 'gemini'

    OpenRouter is the default — it's OpenAI-compatible, so we just
    point the base_url at https://openrouter.ai/api/v1 and use your
    OPENROUTER_API_KEY. Pick any model from openrouter.ai/models.
    """
    provider = os.getenv("LLM_PROVIDER", "openrouter").lower()

    if provider == "openrouter":
        from openai import OpenAI
        client = OpenAI(
            api_key=os.getenv("OPENROUTER_API_KEY"),
            base_url="https://openrouter.ai/api/v1",
        )
        model = os.getenv("LLM_MODEL", "meta-llama/llama-3.1-8b-instruct:free")

        def stream(messages):
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                stream=True,
                extra_headers={
                    # Optional but recommended by OpenRouter
                    "HTTP-Referer": os.getenv("APP_URL", "http://localhost:8501"),
                    "X-Title": os.getenv("APP_NAME", "AI Chat App"),
                },
            )
            for chunk in response:
                delta = chunk.choices[0].delta.content
                if delta:
                    yield delta

        return stream

    elif provider == "openai":
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        model = os.getenv("LLM_MODEL", "gpt-4o-mini")

        def stream(messages):
            response = client.chat.completions.create(
                model=model, messages=messages, stream=True,
            )
            for chunk in response:
                delta = chunk.choices[0].delta.content
                if delta:
                    yield delta

        return stream

    else:
        raise ValueError(f"Unsupported LLM_PROVIDER: {provider}")


# ─── Schemas ──────────────────────────────────────────────────────────────────

class ThreadCreate(BaseModel):
    title: str = "New Chat"


class ChatRequest(BaseModel):
    thread_id: int
    message: str


# ─── Endpoints ────────────────────────────────────────────────────────────────

@app.post("/threads")
def api_create_thread(body: ThreadCreate, db: Session = Depends(get_db)):
    thread = create_thread(db, title=body.title)
    return {"id": thread.id, "title": thread.title, "created_at": thread.created_at}


@app.get("/threads")
def api_list_threads(db: Session = Depends(get_db)):
    threads = get_threads(db)
    return [{"id": t.id, "title": t.title, "created_at": t.created_at} for t in threads]


@app.get("/threads/{thread_id}")
def api_get_thread(thread_id: int, db: Session = Depends(get_db)):
    thread = get_thread(db, thread_id)
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    msgs = get_messages(db, thread_id)
    return {
        "id": thread.id,
        "title": thread.title,
        "created_at": thread.created_at,
        "messages": [
            {"role": m.role, "content": m.content, "timestamp": m.timestamp}
            for m in msgs
        ],
    }


@app.delete("/threads/{thread_id}")
def api_delete_thread(thread_id: int, db: Session = Depends(get_db)):
    success = delete_thread(db, thread_id)
    if not success:
        raise HTTPException(status_code=404, detail="Thread not found")
    return {"detail": "Thread deleted"}


@app.post("/chat")
def api_chat(body: ChatRequest, db: Session = Depends(get_db)):
    """
    Send a message and stream back the AI response.
    Builds context from:
      1. Universal memory (global, persists across threads)
      2. Full message history of the current thread
    After response, distills a brief summary into UniversalMemory.
    """
    thread = get_thread(db, body.thread_id)
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")

    # Persist user message
    add_message(db, body.thread_id, "user", body.message)

    # Auto-title thread on first message
    if thread.title == "New Chat":
        short_title = body.message[:40] + ("…" if len(body.message) > 40 else "")
        thread.title = short_title
        db.commit()

    # Build message list for LLM
    universal_mem = get_universal_memory(db)
    system_content = "You are a helpful AI assistant with persistent memory across conversations.\n\n"

    if universal_mem:
        system_content += (
            "IMPORTANT — the following facts were learned from previous conversations. "
            "Treat them as true and use them when relevant. Do NOT say you don't know "
            "things that are listed here:\n\n"
        )
        for mem in universal_mem:
            system_content += f"- {mem.content}\n"
    else:
        system_content += "No prior memory yet.\n"

    messages = [{"role": "system", "content": system_content}]

    # Add current thread history
    history = get_messages(db, body.thread_id)
    for m in history:
        messages.append({"role": m.role, "content": m.content})

    stream_fn = get_llm_client()

    def generate():
        full_response = ""
        try:
            for chunk in stream_fn(messages):
                full_response += chunk
                yield chunk
        finally:
            if full_response:
                # Persist assistant response
                add_message(db, body.thread_id, "assistant", full_response)

                # Distill a short memory entry into UniversalMemory
                _distill_memory(db, body.thread_id, body.message, full_response)

    return StreamingResponse(generate(), media_type="text/plain")


def _distill_memory(db, thread_id: int, user_msg: str, assistant_msg: str):
    """
    Extracts memorable facts from the exchange and stores them in UniversalMemory.
    Covers names, preferences, job, location, and anything the user asks to remember.
    Stores as clean factual statements so the LLM can directly use them.
    """
    lower = user_msg.lower().strip()

    facts = []

    # Name detection
    for pattern in ["my name is ", "i am called ", "call me ", "i'm called "]:
        if pattern in lower:
            idx = lower.index(pattern) + len(pattern)
            name = user_msg[idx:].split()[0].strip(".,!?")
            if name:
                facts.append(f"The user's name is {name}.")

    # Profession / work
    for pattern in ["i work at ", "i work as ", "i am a ", "i'm a ", "my job is ", "i work for "]:
        if pattern in lower:
            idx = lower.index(pattern) + len(pattern)
            detail = user_msg[idx:idx + 60].split(".")[0].strip()
            if detail:
                facts.append(f"The user works as/at: {detail}.")

    # Location
    for pattern in ["i live in ", "i'm from ", "i am from ", "i'm based in "]:
        if pattern in lower:
            idx = lower.index(pattern) + len(pattern)
            detail = user_msg[idx:idx + 40].split(".")[0].strip()
            if detail:
                facts.append(f"The user lives in / is from: {detail}.")

    # Preferences
    for pattern in ["i like ", "i love ", "i prefer ", "i enjoy ", "i hate ", "i dislike "]:
        if pattern in lower:
            idx = lower.index(pattern) + len(pattern)
            detail = user_msg[idx:idx + 60].split(".")[0].strip()
            if detail:
                facts.append(f"The user said they {pattern.strip()}: {detail}.")

    # Explicit remember requests
    for pattern in ["remember that ", "remember: ", "note that ", "keep in mind "]:
        if pattern in lower:
            idx = lower.index(pattern) + len(pattern)
            detail = user_msg[idx:idx + 120].strip()
            if detail:
                facts.append(f"User asked to remember: {detail}")

    # Fallback: save whole message if it's short and clearly personal
    if not facts:
        personal_keywords = ["my name", "i am", "i'm", "my project", "my company"]
        if any(kw in lower for kw in personal_keywords) and len(user_msg) < 120:
            facts.append(f"User said: {user_msg.strip()}")

    for fact in facts:
        add_universal_memory(db, fact, source_thread_id=thread_id)
