# Team Dashboard Host

A simple, password-protected web app for sharing HTML dashboards with your team.

---

## How it works

| URL | Who uses it | Password |
|---|---|---|
| `yoursite.com/` | Everyone on the team | Viewer password (e.g. project name) |
| `yoursite.com/admin` | Whoever manages dashboards | Admin password |

- **Admin** uploads an `.html` file → it instantly appears at the main URL for viewers
- **Admin** clicks "Clear Dashboard" when review is done → viewers see "nothing active"

---

## One-time setup on Render.com (~10 minutes)

### 1. Put the code on GitHub
1. Go to [github.com](https://github.com) and create a free account if you don't have one
2. Click the **+** button → **New repository** → name it `team-dashboard` → Create
3. Upload all the files from this zip into that repository (drag & drop on the GitHub page)

### 2. Deploy on Render
1. Go to [render.com](https://render.com) and sign up (free) with your GitHub account
2. Click **New +** → **Web Service**
3. Connect your `team-dashboard` GitHub repository
4. Render will auto-detect the settings from `render.yaml`
5. Before clicking Deploy, scroll to **Environment Variables** and add:
   - `ADMIN_PASSWORD` → your chosen admin password
   - `VIEWER_PASSWORD` → the project name (or whatever you want viewers to type)
6. Click **Create Web Service**

Render gives you a free URL like `team-dashboard.onrender.com`. That's your permanent link.

---

## Day-to-day use (no tech knowledge needed)

**To share a dashboard:**
1. Go to `yoursite.com/admin`
2. Enter the admin password
3. Click the upload area, pick your `.html` file
4. Click **Upload & Go Live** — done! Share the main URL + viewer password with the team.

**To clear it:**
1. Go back to `/admin`
2. Click **Clear Dashboard**

---

## Notes

- Files are stored temporarily. If the server restarts, the current dashboard is cleared automatically (just re-upload if needed).
- The free tier on Render may take ~30 seconds to wake up after inactivity. Upgrade to Starter ($7/month) for always-on.
- Only `.html` files can be uploaded.
