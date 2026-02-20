#!/usr/bin/env python3
# -----------------------------------------------------------------------------
"""
ACL management web UI pages.

GET  /webs/{web}/acl                    — view/edit web-level ACL
POST /webs/{web}/acl                    — save web-level ACL
GET  /webs/{web}/topics/{topic}/acl     — view/edit topic-level ACL
POST /webs/{web}/topics/{topic}/acl     — save topic-level ACL
"""
# -----------------------------------------------------------------------------

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services import acl as acl_svc
from app.services import webs as web_svc
from app.services import topics as topic_svc
from app.services.users import get_user_by_id
from webui.context import PageContext
from webui.session import get_current_user
from webui.templating import templates

router = APIRouter(tags=["webui-acl"])


# ── Web ACL ───────────────────────────────────────────────────────────────────

@router.get("/webs/{web_name}/acl", response_class=HTMLResponse)
async def web_acl_page(
    web_name: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    user = await get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    if not user.get("is_admin"):
        ctx = PageContext(title="Forbidden", user=user)
        return templates.TemplateResponse("error.html", {
            **ctx.to_dict(request),
            "message": "Admin access required to manage ACLs.",
        }, status_code=403)

    web = await web_svc.get_web_by_name(db, web_name)
    entries = await acl_svc.get_acl(db, "web", web.id)
    ctx = PageContext(title=f"ACL — {web_name}", user=user, web=web_name)
    return templates.TemplateResponse("acl/edit.html", {
        **ctx.to_dict(request),
        "resource_label": f"Web: {web_name}",
        "save_url": f"/webs/{web_name}/acl",
        "cancel_url": f"/webs/{web_name}",
        "entries": entries,
        "error": "",
    })


@router.post("/webs/{web_name}/acl")
async def web_acl_save(
    web_name: str,
    request: Request,
    entries_json: str = Form(default="[]"),
    db: AsyncSession = Depends(get_db),
):
    user = await get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    if not user.get("is_admin"):
        return RedirectResponse(url=f"/webs/{web_name}", status_code=302)

    web = await web_svc.get_web_by_name(db, web_name)
    try:
        raw = json.loads(entries_json)
        from app.schemas import ACLUpdate, ACLEntry
        data = ACLUpdate(entries=[ACLEntry(**e) for e in raw])
        await acl_svc.set_acl(db, "web", web.id, data)
        return RedirectResponse(url=f"/webs/{web_name}", status_code=302)
    except Exception as e:
        entries = await acl_svc.get_acl(db, "web", web.id)
        ctx = PageContext(title=f"ACL — {web_name}", user=user, web=web_name)
        return templates.TemplateResponse("acl/edit.html", {
            **ctx.to_dict(request),
            "resource_label": f"Web: {web_name}",
            "save_url": f"/webs/{web_name}/acl",
            "cancel_url": f"/webs/{web_name}",
            "entries": entries,
            "error": str(e),
        }, status_code=400)


# ── Topic ACL ─────────────────────────────────────────────────────────────────

@router.get("/webs/{web_name}/topics/{topic_name}/acl", response_class=HTMLResponse)
async def topic_acl_page(
    web_name: str,
    topic_name: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    user = await get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    if not user.get("is_admin"):
        ctx = PageContext(title="Forbidden", user=user)
        return templates.TemplateResponse("error.html", {
            **ctx.to_dict(request),
            "message": "Admin access required to manage ACLs.",
        }, status_code=403)

    topic, _ver = await topic_svc.get_topic(db, web_name, topic_name)
    entries = await acl_svc.get_acl(db, "topic", topic.id)
    ctx = PageContext(title=f"ACL — {web_name}.{topic_name}", user=user, web=web_name, topic=topic_name)
    return templates.TemplateResponse("acl/edit.html", {
        **ctx.to_dict(request),
        "resource_label": f"Topic: {web_name}.{topic_name}",
        "save_url": f"/webs/{web_name}/topics/{topic_name}/acl",
        "cancel_url": f"/webs/{web_name}/topics/{topic_name}",
        "entries": entries,
        "error": "",
    })


@router.post("/webs/{web_name}/topics/{topic_name}/acl")
async def topic_acl_save(
    web_name: str,
    topic_name: str,
    request: Request,
    entries_json: str = Form(default="[]"),
    db: AsyncSession = Depends(get_db),
):
    user = await get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    if not user.get("is_admin"):
        return RedirectResponse(url=f"/webs/{web_name}/topics/{topic_name}", status_code=302)

    topic, _ver = await topic_svc.get_topic(db, web_name, topic_name)
    try:
        raw = json.loads(entries_json)
        from app.schemas import ACLUpdate, ACLEntry
        data = ACLUpdate(entries=[ACLEntry(**e) for e in raw])
        await acl_svc.set_acl(db, "topic", topic.id, data)
        return RedirectResponse(url=f"/webs/{web_name}/topics/{topic_name}", status_code=302)
    except Exception as e:
        entries = await acl_svc.get_acl(db, "topic", topic.id)
        ctx = PageContext(title=f"ACL — {web_name}.{topic_name}", user=user, web=web_name, topic=topic_name)
        return templates.TemplateResponse("acl/edit.html", {
            **ctx.to_dict(request),
            "resource_label": f"Topic: {web_name}.{topic_name}",
            "save_url": f"/webs/{web_name}/topics/{topic_name}/acl",
            "cancel_url": f"/webs/{web_name}/topics/{topic_name}",
            "entries": entries,
            "error": str(e),
        }, status_code=400)
