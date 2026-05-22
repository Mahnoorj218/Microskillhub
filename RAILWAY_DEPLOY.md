# Railway Deploy — MicroSkillHub

## Build fail ka main reason (fix ho chuka)

Git mein **`Backend/venv/`** (hazaron files) aur **`Backend/.env`** commit ho gaye the.
Railway image build is par **fail / timeout** ho jati hai.

**Ab repo se hata diya** — GitHub par naya commit push karo.

---

## Railway settings

| Setting | Value |
|---------|--------|
| **Root Directory** | `Backend` |
| **Start Command** | `uvicorn main:app --host 0.0.0.0 --port $PORT` |

`Backend/railway.toml` auto-config ke liye repo mein hai.

---

## Variables (Railway → Variables tab)

`.env` file push **mat** karo. Yahan set karo:

| Variable | Required |
|----------|----------|
| `SUPABASE_URL` | Yes |
| `SUPABASE_SERVICE_ROLE_KEY` | Yes |
| `GEMINI_API_KEY` | Yes |
| `CORS_ORIGINS` | `*` |

---

## Push steps

```powershell
cd C:\Users\obaid\Microskillhub
git add .gitignore Backend/railway.toml Backend/runtime.txt
git commit -m "Fix Railway deploy: remove venv from git, add railway config"
git push
```

Phir Railway par **Redeploy**.

---

## Agar phir fail ho

1. **Build logs** kholo (View logs) — last red line screenshot bhejo
2. Railway yellow banner: platform outage ho to thori der baad retry
3. **Settings → Root Directory** = `Backend` confirm karo
4. Purani `.env` Git history mein hai — keys rotate karo Supabase/Gemini mein

---

## Live URLs

- App: `https://YOUR-APP.up.railway.app/`
- Health: `https://YOUR-APP.up.railway.app/api/health`
