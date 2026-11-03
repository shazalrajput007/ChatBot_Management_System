# 💬 AI User Management Chatbot (Role-Based)

An AI-powered **Admin & User Chatbot** built with **FastAPI**, **LangChain (Groq)**, and **SQLite**.  
The application allows an administrator to perform complete **CRUD operations** (Create, Read, Update, Delete) on users simply by chatting in plain English, while regular registered users get a clean, general-purpose AI chat interface without any access to sensitive user data.

---

## ✨ Key Features

- **Passwordless Email Login:** Anyone whose email is registered in the database can log in. On first run, the default admin account (`ADMIN_EMAIL`) is created automatically.
- **Role-Based Access Control (Admin vs. User):**
  - **🛡️ Admin (`ADMIN_EMAIL`):**
    - Full **CRUD** on users via natural language chat (Add, Update, Delete, Find, List).
    - Live **Users Sidebar** that updates automatically after every chat command.
    - Quick-action prompt chips for common tasks.
  - **👤 Normal User (any other registered email):**
    - Can log in and chat with a friendly, general-purpose AI assistant.
    - **Zero authority** to view, add, update, or delete users (enforced on both the UI and backend API/LLM tools).
- **Safety Guards:** Prevents the admin from accidentally deleting their own account or locking themselves out.

---

## 🛠️ Tech Stack

| Layer | Technology |
| :--- | :--- |
| **Backend Framework** | Python, FastAPI, Uvicorn |
| **AI / LLM Orchestration** | LangChain (`langchain-core`, `langchain-groq`) |
| **LLM Provider** | Groq API (Default model: `openai/gpt-oss-120b`) |
| **Database** | SQLite3 (auto-initialized on startup) |
| **Frontend** | HTML5, CSS3, Vanilla JavaScript (Single-Page UI) |
| **Configuration** | `python-dotenv`, Pydantic |



"""
Create & Activate a Virtual Environment
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
"""

"""
Install Dependencies
pip install -r requirements.txt
"""