# MicroSkillHub — Render par Deploy Guide

Yeh project **ek hi Web Service** se deploy hota hai: FastAPI backend + Frontend dono same server se (`/` par UI, `/api` par API).

---

## Render settings (copy-paste)

Dashboard → **New +** → **Web Service** → GitHub repo connect karo.

| Field | Value |
|--------|--------|
| **Name** | `microskillhub` (ya jo chaho) |
| **Region** | Singapore / Frankfurt (Pakistan ke qareeb) |
| **Branch** | `main` |
| **Root Directory** | `Backend` |
| **Runtime** | `Python 3` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `uvicorn main:app --host 0.0.0.0 --port $PORT` |
| **Health Check Path** | `/api/health` |

### Root Directory kyun `Backend`?

- `main.py`, `requirements.txt`, aur Python code **`Backend`** folder mein hai.
- Agar Root Directory **khali** chhoroge (repo root), to Render `main.py` nahi dhundhega aur build fail ho jayega.
- Frontend folder repo root par hai (`Frontend/`) — code automatically `../Frontend` se serve hoti hai; alag service ki zaroorat nahi.

---

## Environment Variables (Render → Environment)

| Key | Required | Example / Notes |
|-----|----------|-----------------|
| `SUPABASE_URL` | Yes | `https://xxxxx.supabase.co` |
| `SUPABASE_SERVICE_ROLE_KEY` | Yes | Supabase → Settings → API → **service_role** (secret) |
| `SUPABASE_ANON_KEY` | Optional | anon public key |
| `GEMINI_API_KEY` | Yes (AI chat) | Google AI Studio key |
| `CORS_ORIGINS` | Optional | `*` ya apni Render URL |
| `PYTHON_VERSION` | Recommended | `3.13.0` |

**Important:** `.env` file Git par push **mat** karo. Sirf Render dashboard mein variables set karo.

---

## Pehle Supabase ready karo

1. [supabase.com](https://supabase.com) → project banao  
2. **SQL Editor** → `supabase/migrations/001_initial.sql` run karo  
3. **Authentication → Email** → “Confirm email” **OFF** (dev/testing)  
4. Local se seed (optional):
   ```powershell
   cd Backend
   .\venv\Scripts\python.exe seed_supabase.py
   ```

---

## Step-by-step deploy

### 1. GitHub par code push

```bash
git add .
git commit -m "Prepare for Render deploy"
git push origin main
```

### 2. Render Web Service banao

1. [dashboard.render.com](https://dashboard.render.com) → login  
2. **New +** → **Web Service**  
3. Apna `Microskillhub` repo select karo  
4. Upar wali table ki values bharo (**Root Directory = `Backend`**)  
5. **Environment** section mein Supabase + Gemini keys add karo  
6. **Create Web Service**

### 3. Deploy wait karo

- **Logs** tab mein dekho: `Build successful` → `Uvicorn running`  
- URL milega: `https://microskillhub-xxxx.onrender.com`

### 4. Live test

| Test | URL |
|------|-----|
| App UI | `https://YOUR-APP.onrender.com/` |
| Health | `https://YOUR-APP.onrender.com/api/health` |
| API docs | `https://YOUR-APP.onrender.com/docs` |

Admin login (agar seed kiya ho):

- Email: `admin@microskillhub.com`  
- Password: `admin123`  
- Role: **Platform Administrator**

---

## Free tier notes

- **Cold start:** 15+ min inactive ke baad pehli request slow ho sakti hai (~30–60 sec).  
- **Sleep:** Free web service idle par band ho jati hai — demo ke liye theek, production ke liye paid plan consider karo.  
- **HTTPS:** Render automatically deta hai — extra setup nahi.

---

## Common errors

| Error | Fix |
|-------|-----|
| `No module named 'main'` | Root Directory **`Backend`** set karo |
| `Missing SUPABASE_URL` | Environment variables check karo |
| Build fail `pydantic-core` | `PYTHON_VERSION` = `3.13.0` set karo |
| Frontend blank / 404 | Repo mein `Frontend/` folder push ho; health check `/api/health` |
| Login fail on live URL | Supabase keys sahi hon; email confirm OFF |
| Port error locally | Render par `$PORT` use hota hai — Start Command upar wala rakho |

---

## Optional: `render.yaml` (Blueprint)

Repo root par `render.yaml` hai — **Blueprint Deploy** se auto-config ho sakti hai:

1. Render → **New +** → **Blueprint**  
2. Repo select → file detect → deploy  

Manual settings aur Blueprint dono same `Backend` root use karte hain.

---

## Deploy ke baad checklist

- [ ] `https://YOUR-APP.onrender.com/api/health` → `{"status":"ok","frontend":true}`  
- [ ] Homepage load hoti hai  
- [ ] Admin login + Admin Console data dikhta hai  
- [ ] Student register / login kaam karta hai  
- [ ] Supabase dashboard mein naye users/tasks dikh rahe hain  

---

## Architecture (production)

```
User Browser
    ↓ HTTPS
Render Web Service (Python)
    ├── /          → Frontend (index.html, app.js)
    ├── /api/*     → FastAPI + Supabase
    └── /docs      → Swagger
         ↓
    Supabase (Auth + PostgreSQL)
    Gemini API (AI chat)
```

Koi alag **Static Site** ya **second service** Render par banane ki zaroorat nahi.
