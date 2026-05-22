# Railway Deploy — MicroSkillHub

## Build fail ka main reason (fix ho chuka)

Git mein **`Backend/venv/`** (hazaron files) aur **`Backend/.env`** commit ho gaye the.
Railway image build is par **fail / timeout** ho jati hai.

**Ab repo se hata diya** — GitHub par naya commit push karo.

---

## Railway settings (IMPORTANT — updated)

| Setting | Value |
|---------|--------|
| **Root Directory** | `/` (repo root — **khali** chhoro ya `.`) |
| **Builder** | Dockerfile (auto from `railway.toml`) |
| **Start Command** | *(khali — Dockerfile CMD use hoti hai)* |

**Root Directory `Backend` mat rakho** — `Frontend/` folder alag hai; Docker image dono copy karti hai.

Repo root par `Dockerfile` + `railway.toml` hain.

---

## Variables (Railway → Variables tab)

`.env` file push **mat** karo. Yahan set karo:

| Variable | Required |
|----------|----------|
| `SUPABASE_URL` | Yes — `https://xxxx.supabase.co` |
| `SUPABASE_SERVICE_ROLE_KEY` | Yes — **service_role** secret only |
| `GEMINI_API_KEY` | Yes |
| `CORS_ORIGINS` | `*` |

### `SUPABASE_SERVICE_ROLE_KEY` — common mistake

Supabase API page par **do** keys hain:

| Key name | Use in Railway? |
|----------|-----------------|
| `anon` `public` | **NO** — is se "admin API blocked" / 403 aata hai |
| `service_role` `secret` | **YES** — is variable mein yahi paste karo |

Verify after deploy:

`https://YOUR-APP.up.railway.app/api/health`

```json
{
  "status": "ok",
  "supabase_key_role": "service_role",
  "admin_api_ok": true
}
```

Agar `supabase_key_role` = `anon` ya `admin_api_ok` = `false` → galat key Variables mein hai → fix → **Redeploy**.

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
