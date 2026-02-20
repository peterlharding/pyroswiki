#!/usr/bin/env python
# -----------------------------------------------------------------------------
"""
Plugin Manager
==============
Loads plugins from the ``plugins/`` directory and dispatches lifecycle hooks.

A plugin is a Python module in ``plugins/`` that defines a class named
``Plugin`` inheriting from ``BasePlugin``.  Any hooks the plugin wants to
handle are implemented as async methods.

Available hooks
---------------
pre_render(text, ctx)           → str
    Called before macro expansion.  Return modified text.

post_render(html, ctx)          → str
    Called after Markdown→HTML.  Return modified HTML.

after_save(web, topic, version, user)   → None
    Called after a topic version is saved.

after_create(web, topic, version, user) → None
    Called after a topic is first created.

after_delete(web, topic, user)          → None
    Called after a topic is deleted.

after_upload(web, topic, attachment)    → None
    Called after a file is uploaded.

Example plugin (plugins/my_plugin.py)::

    from app.services.plugins import BasePlugin

    class Plugin(BasePlugin):
        name = "my_plugin"
        enabled = True

        async def post_render(self, html: str, ctx) -> str:
            return html.replace("foo", "bar")
"""
# -----------------------------------------------------------------------------

from __future__ import annotations

import importlib.util
import logging
import sys
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


# -----------------------------------------------------------------------------

class BasePlugin:
    """Base class for all plugins.  Override only the hooks you need."""

    name: str = "unnamed"
    enabled: bool = True

    # ── Render hooks ──────────────────────────────────────────────────────

    async def pre_render(self, text: str, ctx: Any) -> str:
        return text

    async def post_render(self, html: str, ctx: Any) -> str:
        return html

    # ── Topic lifecycle hooks ─────────────────────────────────────────────

    async def after_save(
        self,
        web: str,
        topic: str,
        version: Any,
        user: Optional[Any] = None,
    ) -> None:
        pass

    async def after_create(
        self,
        web: str,
        topic: str,
        version: Any,
        user: Optional[Any] = None,
    ) -> None:
        pass

    async def after_delete(
        self,
        web: str,
        topic: str,
        user: Optional[Any] = None,
    ) -> None:
        pass

    # ── Attachment hooks ──────────────────────────────────────────────────

    async def after_upload(
        self,
        web: str,
        topic: str,
        attachment: Any,
    ) -> None:
        pass


# -----------------------------------------------------------------------------

class PluginManager:
    """
    Discovers, loads, and dispatches to all enabled plugins.

    Parameters
    ----------
    plugin_dir : Path | str | None
        Directory to scan for plugin modules.  Defaults to ``plugins/``
        relative to the project root.  Pass ``None`` to disable file-based
        discovery (useful in tests).
    """

    def __init__(self, plugin_dir: Optional[Path | str] = None) -> None:
        self._plugins: list[BasePlugin] = []
        self._loaded = False

        if plugin_dir is None:
            # Default: <project_root>/plugins/
            plugin_dir = Path(__file__).parent.parent.parent / "plugins"

        self._plugin_dir = Path(plugin_dir)

    # ── Loading ───────────────────────────────────────────────────────────

    def load(self) -> None:
        """Scan plugin_dir and instantiate all enabled Plugin classes."""
        if self._loaded:
            return
        self._loaded = True

        if not self._plugin_dir.is_dir():
            logger.debug("Plugin directory %s not found — no plugins loaded", self._plugin_dir)
            return

        for path in sorted(self._plugin_dir.glob("*.py")):
            if path.name.startswith("_"):
                continue
            self._load_file(path)

    def _load_file(self, path: Path) -> None:
        module_name = f"_plugin_{path.stem}"
        try:
            spec = importlib.util.spec_from_file_location(module_name, path)
            if spec is None or spec.loader is None:
                return
            mod = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = mod
            spec.loader.exec_module(mod)   # type: ignore[union-attr]

            plugin_cls = getattr(mod, "Plugin", None)
            if plugin_cls is None:
                logger.debug("No Plugin class in %s — skipping", path.name)
                return
            if not issubclass(plugin_cls, BasePlugin):
                logger.warning("%s.Plugin does not inherit BasePlugin — skipping", path.name)
                return

            instance = plugin_cls()
            if not instance.enabled:
                logger.debug("Plugin %s is disabled — skipping", instance.name)
                return

            self._plugins.append(instance)
            logger.info("Loaded plugin: %s (%s)", instance.name, path.name)

        except Exception as exc:
            logger.error("Failed to load plugin %s: %s", path.name, exc)

    def register(self, plugin: BasePlugin) -> None:
        """Programmatically register a plugin instance (useful for built-ins)."""
        self._plugins.append(plugin)

    # ── Hook dispatch ─────────────────────────────────────────────────────

    async def pre_render(self, text: str, ctx: Any) -> str:
        for plugin in self._plugins:
            try:
                text = await plugin.pre_render(text, ctx)
            except Exception as exc:
                logger.error("Plugin %s pre_render error: %s", plugin.name, exc)
        return text

    async def post_render(self, html: str, ctx: Any) -> str:
        for plugin in self._plugins:
            try:
                html = await plugin.post_render(html, ctx)
            except Exception as exc:
                logger.error("Plugin %s post_render error: %s", plugin.name, exc)
        return html

    async def after_save(self, web: str, topic: str, version: Any, user: Any = None) -> None:
        for plugin in self._plugins:
            try:
                await plugin.after_save(web, topic, version, user)
            except Exception as exc:
                logger.error("Plugin %s after_save error: %s", plugin.name, exc)

    async def after_create(self, web: str, topic: str, version: Any, user: Any = None) -> None:
        for plugin in self._plugins:
            try:
                await plugin.after_create(web, topic, version, user)
            except Exception as exc:
                logger.error("Plugin %s after_create error: %s", plugin.name, exc)

    async def after_delete(self, web: str, topic: str, user: Any = None) -> None:
        for plugin in self._plugins:
            try:
                await plugin.after_delete(web, topic, user)
            except Exception as exc:
                logger.error("Plugin %s after_delete error: %s", plugin.name, exc)

    async def after_upload(self, web: str, topic: str, attachment: Any) -> None:
        for plugin in self._plugins:
            try:
                await plugin.after_upload(web, topic, attachment)
            except Exception as exc:
                logger.error("Plugin %s after_upload error: %s", plugin.name, exc)

    # ── Introspection ─────────────────────────────────────────────────────

    @property
    def plugins(self) -> list[BasePlugin]:
        return list(self._plugins)

    def __len__(self) -> int:
        return len(self._plugins)


# -----------------------------------------------------------------------------
# Singleton — shared across the application

_manager: Optional[PluginManager] = None


def get_plugin_manager() -> PluginManager:
    global _manager
    if _manager is None:
        _manager = PluginManager()
        _manager.load()
    return _manager
