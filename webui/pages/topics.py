#!/usr/bin/env python3
# -----------------------------------------------------------------------------
"""Topic view, create, edit pages."""
# -----------------------------------------------------------------------------

from __future__ import annotations

from fastapi import APIRouter, Depends, Form, Request
from fastapi.exceptions import HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services import topics as topic_svc
from app.services import attachments as att_svc
from app.services import acl as acl_svc
from app.services import webs as web_svc
from app.services.users import get_user_by_id_or_none
from app.schemas import TopicCreate, TopicUpdate
from app.services.renderer import RenderPipeline
from app.core.config import get_settings
from fastapi.responses import PlainTextResponse
from webui.context import PageContext
from webui.session import get_current_user
from webui.templating import templates

router = APIRouter(tags=["webui-topics"])


def _pipeline(db) -> RenderPipeline:
    return RenderPipeline(base_url=get_settings().base_url, db=db)


# -----------------------------------------------------------------------------

@router.get("/webs/{web_name}/topics/new", response_class=HTMLResponse)
async def new_topic_page_first(
    web_name: str,
    request: Request,
):
    user = await get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    ctx = PageContext(title=f"New Topic in {web_name}", user=user, web=web_name)
    return templates.TemplateResponse("topics/edit.html", {
        **ctx.to_dict(request),
        "web": web_name,
        "topic": None,
        "ver": None,
        "error": "",
    })


@router.post("/webs/{web_name}/topics/new")
async def new_topic_submit_first(
    web_name: str,
    request: Request,
    name: str = Form(...),
    content: str = Form(default=""),
    comment: str = Form(default=""),
    db: AsyncSession = Depends(get_db),
):
    user = await get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    try:
        web = await web_svc.get_web_by_name(db, web_name)
        user_obj = await get_user_by_id_or_none(db, user.get("id"))
        if not await acl_svc.check_permission(db, "web", web.id, "create", user_obj):
            ctx = PageContext(title="Forbidden", user=user, web=web_name)
            return templates.TemplateResponse("error.html", {
                **ctx.to_dict(request),
                "message": "You do not have permission to create topics in this web.",
            }, status_code=403)
        data = TopicCreate(name=name, content=content, comment=comment)
        await topic_svc.create_topic(db, web_name, data, author_id=user["id"])
        return RedirectResponse(url=f"/webs/{web_name}/topics/{name}", status_code=302)
    except Exception as e:
        ctx = PageContext(title=f"New Topic in {web_name}", user=user, web=web_name)
        return templates.TemplateResponse("topics/edit.html", {
            **ctx.to_dict(request),
            "web": web_name,
            "topic": None,
            "ver": None,
            "error": str(e),
        }, status_code=400)


# -----------------------------------------------------------------------------

@router.get("/webs/{web_name}/topics/{topic_name}", response_class=HTMLResponse)
async def view_topic(
    web_name: str,
    topic_name: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    user = await get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    try:
        topic, ver = await topic_svc.get_topic(db, web_name, topic_name)
        web = await web_svc.get_web_by_name(db, web_name)
        user_obj = await get_user_by_id_or_none(db, user.get("id") if user else None)
        allowed = await acl_svc.check_topic_permission(db, topic.id, web.id, "view", user_obj)
        if not allowed:
            ctx = PageContext(title="Forbidden", user=user)
            return templates.TemplateResponse("error.html", {
                **ctx.to_dict(request),
                "message": "You do not have permission to view this topic.",
            }, status_code=403)
        if ver.rendered:
            rendered = ver.rendered
        else:
            rendered = await _pipeline(db).render(
                web_name, topic_name, ver.content, current_user=user
            )
        try:
            attachments = await att_svc.list_attachments(db, web_name, topic_name)
        except Exception:
            attachments = []
        ctx = PageContext(title=f"{web_name}.{topic_name}", user=user, web=web_name, topic=topic_name)
        return templates.TemplateResponse("topics/view.html", {
            **ctx.to_dict(request),
            "web": web_name,
            "topic": topic,
            "ver": ver,
            "rendered": rendered,
            "attachments": attachments,
        })
    except HTTPException as e:
        if e.status_code == 404:
            return RedirectResponse(
                url=f"/webs/{web_name}/topics/new?name={topic_name}",
                status_code=302,
            )
        ctx = PageContext(title="Error", user=user)
        return templates.TemplateResponse("error.html", {
            **ctx.to_dict(request),
            "message": e.detail,
        }, status_code=e.status_code)
    except Exception as e:
        ctx = PageContext(title="Error", user=user)
        return templates.TemplateResponse("error.html", {
            **ctx.to_dict(request),
            "message": str(e),
        }, status_code=500)


# -----------------------------------------------------------------------------

@router.get("/webs/{web_name}/topics/{topic_name}/edit", response_class=HTMLResponse)
async def edit_topic_page(
    web_name: str,
    topic_name: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    user = await get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    try:
        topic, ver = await topic_svc.get_topic(db, web_name, topic_name)
        ctx = PageContext(title=f"Edit {web_name}.{topic_name}", user=user, web=web_name, topic=topic_name)
        return templates.TemplateResponse("topics/edit.html", {
            **ctx.to_dict(request),
            "web": web_name,
            "topic": topic,
            "ver": ver,
            "error": "",
        })
    except Exception as e:
        ctx = PageContext(title="Not Found", user=user)
        return templates.TemplateResponse("error.html", {
            **ctx.to_dict(request),
            "message": str(e),
        }, status_code=404)


@router.post("/webs/{web_name}/topics/{topic_name}/edit")
async def edit_topic_submit(
    web_name: str,
    topic_name: str,
    request: Request,
    content: str = Form(default=""),
    comment: str = Form(default=""),
    db: AsyncSession = Depends(get_db),
):
    user = await get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    try:
        topic_obj, _ver = await topic_svc.get_topic(db, web_name, topic_name)
        web = await web_svc.get_web_by_name(db, web_name)
        user_obj = await get_user_by_id_or_none(db, user.get("id"))
        if not await acl_svc.check_topic_permission(db, topic_obj.id, web.id, "edit", user_obj):
            ctx = PageContext(title="Forbidden", user=user, web=web_name, topic=topic_name)
            return templates.TemplateResponse("error.html", {
                **ctx.to_dict(request),
                "message": "You do not have permission to edit this topic.",
            }, status_code=403)
        data = TopicUpdate(content=content, comment=comment)
        await topic_svc.update_topic(db, web_name, topic_name, data, author_id=user["id"])
        return RedirectResponse(url=f"/webs/{web_name}/topics/{topic_name}", status_code=302)
    except Exception as e:
        topic, ver = await topic_svc.get_topic(db, web_name, topic_name)
        ctx = PageContext(title=f"Edit {web_name}.{topic_name}", user=user, web=web_name, topic=topic_name)
        return templates.TemplateResponse("topics/edit.html", {
            **ctx.to_dict(request),
            "web": web_name,
            "topic": topic,
            "ver": ver,
            "error": str(e),
        }, status_code=400)


# -----------------------------------------------------------------------------

@router.get("/webs/{web_name}/topics/{topic_name}/raw", response_class=HTMLResponse)
async def raw_topic(
    web_name: str,
    topic_name: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    user = await get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    try:
        topic, ver = await topic_svc.get_topic(db, web_name, topic_name)
        ctx = PageContext(title=f"Raw — {web_name}.{topic_name}", user=user, web=web_name, topic=topic_name)
        return templates.TemplateResponse("topics/raw.html", {
            **ctx.to_dict(request),
            "web": web_name,
            "topic": topic,
            "ver": ver,
        })
    except Exception as e:
        ctx = PageContext(title="Not Found", user=user)
        return templates.TemplateResponse("error.html", {
            **ctx.to_dict(request),
            "message": str(e),
        }, status_code=404)


# -----------------------------------------------------------------------------

@router.post("/webs/{web_name}/topics/{topic_name}/delete")
async def delete_topic(
    web_name: str,
    topic_name: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    user = await get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    topic_obj, _ver = await topic_svc.get_topic(db, web_name, topic_name)
    web = await web_svc.get_web_by_name(db, web_name)
    user_obj = await get_user_by_id_or_none(db, user.get("id"))
    if not await acl_svc.check_topic_permission(db, topic_obj.id, web.id, "delete", user_obj):
        ctx = PageContext(title="Forbidden", user=user, web=web_name, topic=topic_name)
        return templates.TemplateResponse("error.html", {
            **ctx.to_dict(request),
            "message": "You do not have permission to delete this topic.",
        }, status_code=403)
    await topic_svc.delete_topic(db, web_name, topic_name)
    return RedirectResponse(url=f"/webs/{web_name}", status_code=302)


# -----------------------------------------------------------------------------

@router.get("/webs/{web_name}/topics/{topic_name}/history", response_class=HTMLResponse)
async def topic_history(
    web_name: str,
    topic_name: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    user = await get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    topic, _ = await topic_svc.get_topic(db, web_name, topic_name)
    versions = await topic_svc.get_topic_history(db, web_name, topic_name)
    ctx = PageContext(title=f"History — {web_name}.{topic_name}", user=user, web=web_name, topic=topic_name)
    return templates.TemplateResponse("topics/history.html", {
        **ctx.to_dict(request),
        "web": web_name,
        "topic": topic,
        "versions": versions,
    })
