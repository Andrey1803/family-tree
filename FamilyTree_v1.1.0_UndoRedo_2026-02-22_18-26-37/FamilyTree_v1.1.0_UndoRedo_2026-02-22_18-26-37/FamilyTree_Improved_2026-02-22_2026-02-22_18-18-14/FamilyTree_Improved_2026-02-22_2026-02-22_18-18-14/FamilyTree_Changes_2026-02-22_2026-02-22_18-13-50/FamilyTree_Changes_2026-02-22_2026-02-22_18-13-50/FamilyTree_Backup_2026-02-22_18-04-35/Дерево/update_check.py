# -*- coding: utf-8 -*-
"""Проверка обновлений: GitHub API (надёжно) или запасной URL."""

import json
import sys
import threading
from pathlib import Path

try:
    import urllib.request
except ImportError:
    urllib = None


def _get_local_version():
    """Текущая версия приложения."""
    try:
        import version
        return getattr(version, "__version__", None) or getattr(version, "VERSION", "0.0.0")
    except ImportError:
        pass
    try:
        root = Path(sys._MEIPASS) if getattr(sys, "frozen", False) else Path(__file__).resolve().parent.parent
        vfile = root / "version.py"
        if vfile.exists():
            for line in vfile.read_text(encoding="utf-8").splitlines():
                if "__version__" in line or "VERSION" in line:
                    return line.split("=")[1].strip().strip("'\"")
    except Exception:
        pass
    return "0.0.0"


def _parse_version(s):
    """Преобразует '1.0.2' в (1, 0, 2)."""
    try:
        return tuple(int(x) for x in str(s).split(".")[:3])
    except (ValueError, TypeError):
        return (0, 0, 0)


def _is_newer(server_ver, local_ver):
    return _parse_version(server_ver) > _parse_version(local_ver)


def check_for_updates(server_url, on_update, root, on_no_update=None, on_error=None, github_repo=None):
    """
    Проверяет обновления: сначала GitHub API, при ошибке — server_url/api/version.
    github_repo: "owner/repo" для GitHub (например "Andrey1803/family-tree").
    """
    if not urllib:
        if on_error:
            root.after(0, on_error)
        return

    repo = github_repo or getattr(
        __import__("constants", fromlist=["GITHUB_REPO"]),
        "GITHUB_REPO", "Andrey1803/family-tree"
    )

    def _check():
        # 1. Пробуем GitHub API
        try:
            url = f"https://api.github.com/repos/{repo}/releases/latest"
            req = urllib.request.Request(url, headers={"User-Agent": "FamilyTree/1.0", "Accept": "application/vnd.github.v3+json"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode())
            server_ver = data.get("tag_name", "0.0.0").lstrip("v")
            assets = data.get("assets", [])
            download_url = f"https://github.com/{repo}/releases/latest"
            for a in assets:
                if a.get("name", "").endswith((".exe", ".zip")):
                    download_url = a.get("browser_download_url", download_url)
                    break
            local = _get_local_version()
            if _is_newer(server_ver, local):
                root.after(0, lambda: on_update(server_ver, download_url))
            elif on_no_update:
                root.after(0, on_no_update)
            return
        except Exception:
            pass
        # 2. Запасной вариант: server_url
        try:
            url = f"{server_url.rstrip('/')}/api/version"
            req = urllib.request.Request(url, headers={"User-Agent": "FamilyTree/1.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode())
            server_ver = data.get("version", "0.0.0")
            download_url = data.get("download_url", url)
            if _is_newer(server_ver, _get_local_version()):
                root.after(0, lambda: on_update(server_ver, download_url))
            elif on_no_update:
                root.after(0, on_no_update)
            return
        except Exception:
            pass
        if on_error:
            root.after(0, on_error)

    threading.Thread(target=_check, daemon=True).start()
