"""Google OAuth for business owners - login with Google to access Business Profile."""
import os
import urllib.parse
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
import httpx

router = APIRouter(prefix="/auth/google", tags=["google-auth"])

GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")
REDIRECT_URI = "https://ai-agency-platform.onrender.com/api/auth/google/callback"

SCOPES = [
    "openid",
    "email",
    "profile",
    "https://www.googleapis.com/auth/business.manage",
    "https://www.googleapis.com/auth/calendar",
]


@router.get("/login")
def google_login(website_id: str = ""):
    """Redirect to Google OAuth consent screen."""
    if not GOOGLE_CLIENT_ID:
        raise HTTPException(500, "Google OAuth not configured")
    
    state = website_id  # Pass website_id through state
    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": " ".join(SCOPES),
        "access_type": "offline",
        "prompt": "consent",
        "state": state,
    }
    url = "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode(params)
    return RedirectResponse(url)


@router.get("/callback")
async def google_callback(code: str = "", state: str = "", error: str = ""):
    """Handle Google OAuth callback."""
    if error:
        return HTMLResponse(f"<h1>Login Failed</h1><p>{error}</p>")
    if not code:
        return HTMLResponse("<h1>No code received</h1>")
    
    # Exchange code for tokens
    async with httpx.AsyncClient() as client:
        resp = await client.post("https://oauth2.googleapis.com/token", data={
            "code": code,
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "redirect_uri": REDIRECT_URI,
            "grant_type": "authorization_code",
        })
        if resp.status_code != 200:
            return HTMLResponse(f"<h1>Token Error</h1><p>{resp.text[:200]}</p>")
        tokens = resp.json()
    
    access_token = tokens.get("access_token", "")
    refresh_token = tokens.get("refresh_token", "")
    
    # Get user info
    async with httpx.AsyncClient() as client:
        user_resp = await client.get("https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"})
        user = user_resp.json() if user_resp.status_code == 200 else {}
    
    email = user.get("email", "")
    name = user.get("name", "")
    picture = user.get("picture", "")
    website_id = state
    
    # Store tokens in supabase for this website/business
    if website_id:
        try:
            from app.core.supabase import get_supabase
            db = get_supabase()
            db.table("google_auth_tokens").upsert({
                "website_id": website_id,
                "email": email,
                "name": name,
                "access_token": access_token,
                "refresh_token": refresh_token,
                "picture": picture,
            }, on_conflict="website_id").execute()
        except Exception:
            pass
    
    # Redirect back to dashboard with success
    redirect_url = f"/api/panel/{website_id}" if website_id else "/"
    return HTMLResponse(f"""<!DOCTYPE html><html><head><meta charset="UTF-8">
<style>*{{margin:0;padding:0;box-sizing:border-box}}body{{font-family:sans-serif;background:#0f172a;color:#fff;display:flex;align-items:center;justify-content:center;min-height:100vh;padding:20px}}.card{{background:rgba(255,255,255,.03);backdrop-filter:blur(12px);border:1px solid rgba(255,255,255,.08);border-radius:16px;padding:24px;text-align:center;max-width:360px}}</style></head><body>
<div class="card">
<img src="{picture}" style="width:60px;height:60px;border-radius:50%;margin-bottom:12px">
<h2 style="font-size:1rem;margin-bottom:4px">Welcome, {name}!</h2>
<p style="font-size:.75rem;color:#64748b;margin-bottom:12px">{email}</p>
<p style="font-size:.8rem;color:#22c55e;margin-bottom:16px">&#10004; Google account connected</p>
<p style="font-size:.7rem;color:#94a3b8;margin-bottom:16px">You can now manage Google Reviews, Calendar bookings, and more from your dashboard.</p>
<a href="{redirect_url}" style="display:inline-block;padding:10px 20px;background:#6366f1;color:#fff;border-radius:8px;font-weight:700;font-size:.85rem;text-decoration:none">Go to Dashboard</a>
</div></body></html>""")


@router.get("/status/{website_id}")
async def google_auth_status(website_id: str):
    """Check if business owner has connected Google."""
    try:
        from app.core.supabase import get_supabase
        db = get_supabase()
        result = db.table("google_auth_tokens").select("email,name,picture").eq("website_id", website_id).limit(1).execute()
        if result.data:
            return {"connected": True, "email": result.data[0].get("email"), "name": result.data[0].get("name")}
    except Exception:
        pass
    return {"connected": False}
