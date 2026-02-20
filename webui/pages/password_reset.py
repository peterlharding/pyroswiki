#!/usr/bin/env python3
# -----------------------------------------------------------------------------
"""
Password reset web UI pages.

GET  /forgot-password              — request reset form
POST /forgot-password              — send reset email
GET  /reset-password?token=...     — set new password form
POST /reset-password               — apply new password
"""
# -----------------------------------------------------------------------------

from __future__ import annotations

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db
from app.services import password_reset as reset_svc
from app.services.email import send_password_reset_email
from webui.context import PageContext
from webui.templating import templates

router = APIRouter(tags=["webui-password-reset"])


# ── Request reset ─────────────────────────────────────────────────────────────

@router.get("/forgot-password", response_class=HTMLResponse)
async def forgot_password_page(request: Request):
    ctx = PageContext(title="Forgot Password", user=None)
    return templates.TemplateResponse("auth/forgot_password.html", {
        **ctx.to_dict(request),
        "submitted": False,
        "error": "",
    })


@router.post("/forgot-password")
async def forgot_password_submit(
    request: Request,
    email: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    settings = get_settings()
    ctx = PageContext(title="Forgot Password", user=None)

    result = await reset_svc.create_reset_token(db, email.strip().lower())

    if result:
        user, raw_token = result
        reset_url = f"{settings.base_url.rstrip('/')}/reset-password?token={raw_token}"
        await send_password_reset_email(
            to=user.email,
            username=user.display_name or user.username,
            reset_url=reset_url,
            site_name=settings.site_name,
        )

    # Always show the same confirmation — don't reveal whether email exists
    return templates.TemplateResponse("auth/forgot_password.html", {
        **ctx.to_dict(request),
        "submitted": True,
        "error": "",
    })


# ── Set new password ──────────────────────────────────────────────────────────

@router.get("/reset-password", response_class=HTMLResponse)
async def reset_password_page(request: Request, token: str = ""):
    if not token:
        ctx = PageContext(title="Invalid Link", user=None)
        return templates.TemplateResponse("error.html", {
            **ctx.to_dict(request),
            "message": "Missing reset token. Please request a new password reset.",
        }, status_code=400)

    ctx = PageContext(title="Reset Password", user=None)
    return templates.TemplateResponse("auth/reset_password.html", {
        **ctx.to_dict(request),
        "token": token,
        "error": "",
        "success": False,
    })


@router.post("/reset-password")
async def reset_password_submit(
    request: Request,
    token: str = Form(...),
    new_password: str = Form(...),
    confirm_password: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    ctx = PageContext(title="Reset Password", user=None)

    if new_password != confirm_password:
        return templates.TemplateResponse("auth/reset_password.html", {
            **ctx.to_dict(request),
            "token": token,
            "error": "Passwords do not match.",
            "success": False,
        }, status_code=400)

    if len(new_password) < 8:
        return templates.TemplateResponse("auth/reset_password.html", {
            **ctx.to_dict(request),
            "token": token,
            "error": "Password must be at least 8 characters.",
            "success": False,
        }, status_code=400)

    try:
        await reset_svc.apply_reset_token(db, token, new_password)
        return templates.TemplateResponse("auth/reset_password.html", {
            **ctx.to_dict(request),
            "token": "",
            "error": "",
            "success": True,
        })
    except Exception as e:
        return templates.TemplateResponse("auth/reset_password.html", {
            **ctx.to_dict(request),
            "token": token,
            "error": str(e),
            "success": False,
        }, status_code=400)
