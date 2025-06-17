# Lyra Backend API

This is the official backend for **Lyra.solutions**, built to demonstrate a minimal viable product (MVP) for pre-seed fundraising. It includes user authentication, a protected dashboard, and a clean API structure using FastAPI.

## 🚀 Features

- ✅ FastAPI-based asynchronous backend
- ✅ JWT-based user authentication
- ✅ Protected `/dashboard` endpoint
- ✅ SQLite support via SQLModel (upgradeable to PostgreSQL)
- ✅ Swagger UI docs auto-generated at `/docs`
- ✅ .env environment variable support

## 🧱 Tech Stack

- **FastAPI** – Modern Python web framework
- **SQLModel** – SQLAlchemy + Pydantic in one ORM
- **JWT (JSON Web Tokens)** – Auth and session management
- **SQLite** – Lightweight DB for local demo
- **Uvicorn** – Lightning-fast ASGI server

## 🛠️ Local Setup

```bash
# Clone the repo
git clone https://github.com/lyrasolutions/lyra-backend.git
cd lyra-backend

# (Optional) Create a virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Initialize the database
python -c "from app.db.session import init_db; init_db()"

# Run the app
uvicorn app.main:app --reload
```

## 🌐 API Access

- **Base URL:** `http://127.0.0.1:8000`
- **Swagger Docs:** `http://127.0.0.1:8000/docs`

## 🔒 Auth Flow

- `POST /auth/register` – Register new user
- `POST /auth/login` – Login with credentials
- `GET /dashboard/` – Protected route (requires Bearer token)

## 🧠 Roadmap

- ⬜ Add email verification
- ⬜ PostgreSQL + production-ready DB setup
- ⬜ Admin panel & user roles
- ⬜ AI integration endpoints (coming soon)
- ⬜ Deployment to Render or Fly.io

## 📩 Contact

For technical questions or business inquiries:

**Justin Chabrier**  
📧 jlconsulting316@gmail.com  
📱 (305) 790-2871  
🌐 [Lyra.solutions](https://lyra.solutions)