# MicroSkillHub — Supabase Setup

Project ab **MySQL ki jagah Supabase** use karta hai:

- **Supabase Auth** — login / register
- **Supabase PostgreSQL** — skills, tasks, applications, XP
- **FastAPI** — API layer (frontend same URLs use karti hai)

---

## 1. Supabase project banao

1. [https://supabase.com](https://supabase.com) par account banao
2. **New project** → naam: `microskillhub`
3. Database password save kar lo

---

## 2. API keys copy karo

**Project Settings → API**

| Key | Use |
|-----|-----|
| Project URL | `SUPABASE_URL` |
| `service_role` (secret) | `SUPABASE_SERVICE_ROLE_KEY` — sirf backend |
| `anon` public | `SUPABASE_ANON_KEY` — optional frontend |

---

## 3. Database schema run karo

**SQL Editor → New query** → poora file paste karo:

`supabase/migrations/001_initial.sql`

→ **Run**

---

## 4. Email settings (register / rate limit)

**Authentication → Providers → Email**

- **Confirm email** = **OFF** (turant login, kam emails)
- Agar `email rate limit exceeded` aaye: **Authentication → Rate Limits** → limits badhao, ya ~1 ghanta wait

Backend register ab confirmation email **nahi** bhejta.

---

## 5. Backend `.env` file

```bash
cd Backend
copy .env.example .env
```

`.env` mein values bharo:

```env
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJhbG...
SUPABASE_ANON_KEY=eyJhbG...
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
GEMINI_API_KEY=your_key
```

---

## 6. Dependencies install

```powershell
cd Backend
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

---

## 7. Admin + sample data seed

```powershell
.\venv\Scripts\python.exe seed_supabase.py
```

Default admin:

- Email: `admin@microskillhub.com`
- Password: `admin123`
- Role: **admin**

---

## 8. Server start karo (sirf backend — frontend bhi isi se chalti hai)

```powershell
cd Backend
.\start.ps1
```

Ya manually:

```powershell
.\venv\Scripts\python.exe -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Browser:

| Page | URL |
|------|-----|
| App (UI) | **http://127.0.0.1:8000** |
| API docs | **http://127.0.0.1:8000/docs** |
| Health | **http://127.0.0.1:8000/api/health** |

Alag se `http.server` ya port 3000 ki zaroorat **nahi**.

---

## Architecture

```
Browser → http://localhost:8000
    ├── /              → Frontend (index.html, app.js)
    ├── /api/*         → FastAPI + Supabase
    └── /docs          → Swagger UI

FastAPI (main.py)
    ↓  supabase-py (service role)
Supabase Auth + PostgreSQL
```

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `Missing SUPABASE_URL` | `.env` check karo |
| Login 401 | Email confirm OFF karo ya email verify karo |
| Register OK but login fail | `profiles` table mein row hai? SQL migration dubara run karo |
| Skills empty | `001_initial.sql` seed skills insert karta hai |
| AI chat error | `GEMINI_API_KEY` set karo |

---

## Purana MySQL

`Backend/schema.sql` ab legacy hai. Naya schema: `supabase/migrations/001_initial.sql`
