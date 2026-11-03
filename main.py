"""Admin Chatbot - FastAPI entry point. Routes only; logic lives in the other modules."""
from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from ai_agent import HISTORY, run_agent
from auth import current_user, login, logout, require_admin
from config import STATIC_DIR
from database import db, init_db, row_to_dict
from user_tools import CURRENT_ADMIN

init_db()

app = FastAPI(title="Admin Chatbot")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


class LoginIn(BaseModel):
    email: str


class ChatIn(BaseModel):
    message: str


@app.get("/")
def index():
    return FileResponse(STATIC_DIR / "index.html")


@app.post("/api/login")
def api_login(body: LoginIn):
    return login(body.email)


@app.get("/api/me")
def api_me(user: dict = Depends(current_user)):
    return {"email": user["email"], "name": user["name"], "role": user["role"]}


@app.post("/api/logout")
def api_logout(user: dict = Depends(current_user)):
    logout(user["token"])
    HISTORY.pop(user["token"], None)
    return {"ok": True}


@app.get("/api/users")
def api_users(_admin: dict = Depends(require_admin)):  # admin only
    with db() as conn:
        rows = conn.execute("SELECT * FROM users ORDER BY id").fetchall()
    return {"users": [row_to_dict(r) for r in rows]}


@app.post("/api/chat")
def api_chat(body: ChatIn, user: dict = Depends(current_user)):
    message = body.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="Message is empty.")
    CURRENT_ADMIN.set(user["email"])
    try:
        reply = run_agent(user["token"], message, user)
    except Exception as exc:
        reply = f"Sorry, I couldn't reach the AI service ({str(exc)[:200]})."
    return {"reply": reply}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)