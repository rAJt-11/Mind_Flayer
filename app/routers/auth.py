"""
routers/auth.py – Login, Signup, and Logout routes.
"""

import logging
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.user import UserProfile
from app.services.auth_service import authenticate_user, create_user, get_user_by_username

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Auth"])
templates = Jinja2Templates(directory="app/templates")


# ─── Login ─────────────────────────────────────────────────────────────────────
@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Serve the login page. Redirect to dashboard if already logged in."""
    if request.session.get("user_id"):
        return RedirectResponse(url="/", status_code=302)
    return templates.TemplateResponse("login.html", {"request": request, "error": None})


@router.post("/login", response_class=HTMLResponse)
async def login_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    user = await authenticate_user(db, username.strip(), password)
    if not user:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Invalid username or password."},
            status_code=401,
        )
    if not user.is_active:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Your account is disabled. Contact support."},
            status_code=403,
        )

    # Set session
    request.session["user_id"] = user.id
    request.session["username"] = user.username
    logger.info(f"User '{user.username}' logged in successfully.")
    return RedirectResponse(url="/", status_code=302)


# ─── Signup ────────────────────────────────────────────────────────────────────
@router.get("/signup", response_class=HTMLResponse)
async def signup_page(request: Request):
    """Serve the signup page. Redirect to dashboard if already logged in."""
    if request.session.get("user_id"):
        return RedirectResponse(url="/", status_code=302)
    return templates.TemplateResponse("signup.html", {"request": request, "error": None})


@router.post("/signup", response_class=HTMLResponse)
async def signup_submit(
    request: Request,
    name: str = Form(...),
    username: str = Form(...),
    email: str = Form(default=None),
    password: str = Form(...),
    confirm_password: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    # Validation
    if len(name.strip()) < 2:
        return templates.TemplateResponse(
            "signup.html",
            {"request": request, "error": "Name must be at least 2 characters."},
            status_code=422,
        )
    if len(username.strip()) < 3 or not username.replace("_", "").isalnum():
        return templates.TemplateResponse(
            "signup.html",
            {"request": request, "error": "Username must be at least 3 alphanumeric characters (underscores allowed)."},
            status_code=422,
        )
    if len(password) < 8:
        return templates.TemplateResponse(
            "signup.html",
            {"request": request, "error": "Password must be at least 8 characters."},
            status_code=422,
        )
    if password != confirm_password:
        return templates.TemplateResponse(
            "signup.html",
            {"request": request, "error": "Passwords do not match."},
            status_code=422,
        )

    # Check username availability
    existing = await get_user_by_username(db, username.strip())
    if existing:
        return templates.TemplateResponse(
            "signup.html",
            {"request": request, "error": f"Username '{username}' is already taken."},
            status_code=409,
        )

    # Create user
    user = await create_user(
        db,
        username=username.strip().lower(),
        password=password,
        name=name.strip(),
        email=email.strip() if email and email.strip() else None,
    )

    # Auto-login after signup
    request.session["user_id"] = user.id
    request.session["username"] = user.username
    logger.info(f"New account created and logged in: '{user.username}'")
    return RedirectResponse(url="/", status_code=302)


# ─── Logout ────────────────────────────────────────────────────────────────────
@router.get("/logout")
async def logout(request: Request):
    username = request.session.get("username", "unknown")
    request.session.clear()
    logger.info(f"User '{username}' logged out.")
    return RedirectResponse(url="/login", status_code=302)
