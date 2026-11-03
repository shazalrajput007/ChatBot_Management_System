"""LangChain tools that manage users. Only the admin may run them."""
import contextvars
import json
from typing import Optional
import contextvars
import json
import sqlite3
from typing import Optional

from langchain_core.tools import tool

from config import EDITABLE_FIELDS, EMAIL_RE, is_admin
from database import db, find_users, name_from_email, row_to_dict

# The admin who is currently chatting (set per request, read by the tools).
CURRENT_ADMIN: contextvars.ContextVar[str] = contextvars.ContextVar("current_admin", default="")


def _result(ok: bool, message: str, **extra) -> str:
    return json.dumps({"ok": ok, "message": message, **extra})


def _ambiguous(rows) -> str:
    return _result(
        False,
        "More than one user matches. Ask the admin which one they mean (use the email).",
        matches=[row_to_dict(r) for r in rows],
    )


def _admin_only() -> Optional[str]:
    """Extra safety: tools refuse to run unless the current requester is the admin."""
    if not is_admin(CURRENT_ADMIN.get()):
        return _result(False, "Permission denied. Only the admin can manage users.")
    return None


@tool
def add_user(email: str, phone: str = "", name: str = "", city: str = "") -> str:
    """Add a new user. Only email is required. phone, name and city are optional."""
    if (denied := _admin_only()):
        return denied
    email = email.strip().strip("\"'").lower()
    if not EMAIL_RE.match(email):
        return _result(False, f"'{email}' is not a valid email address.")
    name = name.strip() or name_from_email(email)
    try:
        with db() as conn:
            conn.execute(
                "INSERT INTO users (email, name, phone, city) VALUES (?, ?, ?, ?)",
                (email, name, phone.strip(), city.strip()),
            )
            row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        return _result(True, "User added.", user=row_to_dict(row))
    except sqlite3.IntegrityError:
        return _result(False, f"A user with email {email} already exists.")


@tool
def delete_user(identifier: str) -> str:
    """Delete a user. identifier is the user's email address or first name / full name."""
    if (denied := _admin_only()):
        return denied
    with db() as conn:
        rows = find_users(conn, identifier)
        if not rows:
            return _result(False, f"No user found matching '{identifier}'.")
        if len(rows) > 1:
            return _ambiguous(rows)
        user = rows[0]
        if is_admin(user["email"]):
            return _result(False, "The admin account cannot be deleted.")
        conn.execute("DELETE FROM users WHERE id = ?", (user["id"],))
        # Log the removed user out everywhere.
        conn.execute("DELETE FROM sessions WHERE lower(email) = ?", (user["email"].lower(),))
    return _result(True, "User deleted.", user=row_to_dict(user))


@tool
def update_user(identifier: str, field: str, new_value: str) -> str:
    """Update one field of an existing user.

    identifier: the user's email or first name / full name (e.g. "samantha").
    field: one of "name", "email", "phone", "city".
    new_value: the new value.
    """
    if (denied := _admin_only()):
        return denied
    field = field.strip().lower()
    if field not in EDITABLE_FIELDS:
        return _result(False, f"Field must be one of: {', '.join(sorted(EDITABLE_FIELDS))}.")
    new_value = new_value.strip().strip("\"'")
    if field == "email":
        new_value = new_value.lower()
        if not EMAIL_RE.match(new_value):
            return _result(False, f"'{new_value}' is not a valid email address.")
    try:
        with db() as conn:
            rows = find_users(conn, identifier)
            if not rows:
                return _result(False, f"No user found matching '{identifier}'.")
            if len(rows) > 1:
                return _ambiguous(rows)
            user = rows[0]
            if field == "email" and is_admin(user["email"]):
                return _result(False, "The admin's email cannot be changed here.")
            # `field` is validated against EDITABLE_FIELDS above, so this is safe.
            conn.execute(f"UPDATE users SET {field} = ? WHERE id = ?", (new_value, user["id"]))
            if field == "email":  # keep that user's sessions valid
                conn.execute(
                    "UPDATE sessions SET email = ? WHERE lower(email) = ?",
                    (new_value, user["email"].lower()),
                )
            row = conn.execute("SELECT * FROM users WHERE id = ?", (user["id"],)).fetchone()
        return _result(True, f"Updated {field}.", user=row_to_dict(row))
    except sqlite3.IntegrityError:
        return _result(False, f"Another user already has the email {new_value}.")


@tool
def find_user(identifier: str) -> str:
    """Look up a user by email or first name / full name and show their details."""
    if (denied := _admin_only()):
        return denied
    with db() as conn:
        rows = find_users(conn, identifier)
    if not rows:
        return _result(False, f"No user found matching '{identifier}'.")
    return _result(True, f"Found {len(rows)} user(s).", users=[row_to_dict(r) for r in rows])


@tool
def list_users() -> str:
    """List every user in the system."""
    if (denied := _admin_only()):
        return denied
    with db() as conn:
        rows = conn.execute("SELECT * FROM users ORDER BY id").fetchall()
    return _result(True, f"{len(rows)} user(s) in total.", users=[row_to_dict(r) for r in rows])


TOOLS = {t.name: t for t in (add_user, delete_user, update_user, find_user, list_users)}