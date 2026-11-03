"""Login, logout, session validation and the admin guard."""
import secrets
from typing import Optional

from fastapi import Depends, Header, HTTPException

from config import is_admin
from database import db


def role_of(email: str) -> str:
    return "admin" if is_admin(email) else "user"


def login(email: str) -> dict:
    email = email.strip().lower()
    with db() as conn:
        user = conn.execute("SELECT * FROM users WHERE lower(email) = ?", (email,)).fetchone()
        if not user:
            raise HTTPException(status_code=401, detail="This email is not registered in the system.")
        token = secrets.token_urlsafe(32)
        conn.execute("INSERT INTO sessions (token, email) VALUES (?, ?)", (token, user["email"]))
    return {
        "token": token,
        "email": user["email"],
        "name": user["name"],
        "role": role_of(user["email"]),
    }


def logout(token: str) -> None:
    with db() as conn:
        conn.execute("DELETE FROM sessions WHERE token = ?", (token,))


def current_user(authorization: Optional[str] = Header(None)) -> dict:
    """FastAPI dependency: resolves 'Authorization: Bearer <token>' to a user."""
    token = (authorization or "").removeprefix("Bearer ").strip()
    if token:
        with db() as conn:
            row = conn.execute(
                """SELECT s.token, u.email, u.name FROM sessions s
                   JOIN users u ON lower(u.email) = lower(s.email) WHERE s.token = ?""",
                (token,),
            ).fetchone()
        if row:
            return {
                "token": row["token"],
                "email": row["email"],
                "name": row["name"],
                "role": role_of(row["email"]),
            }
    raise HTTPException(status_code=401, detail="Please log in again.")


def require_admin(user: dict = Depends(current_user)) -> dict:
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required.")
    return user