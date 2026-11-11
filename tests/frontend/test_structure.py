"""Struktura katalogu frontend/: szablony się kompilują, a importy CSS i JS wskazują istniejące pliki."""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from flask import Flask

from backend import FRONTEND_DIR
from backend.core.constants import USER_COLORS

TEMPLATES_DIR = FRONTEND_DIR / "templates"
STATIC_DIR = FRONTEND_DIR / "static"
TEMPLATE_NAMES = sorted(path.relative_to(TEMPLATES_DIR).as_posix() for path in TEMPLATES_DIR.rglob("*.html"))


def test_flask_uses_frontend_directory(app: Flask) -> None:
    assert Path(app.template_folder) == TEMPLATES_DIR
    assert Path(app.static_folder) == STATIC_DIR


@pytest.mark.parametrize("name", TEMPLATE_NAMES)
def test_template_compiles(app: Flask, name: str) -> None:
    app.jinja_env.get_template(name)


def test_templates_are_grouped() -> None:
    allowed = {"layouts", "components", "pages"}

    assert {name.split("/")[0] for name in TEMPLATE_NAMES} == allowed


def test_css_imports_exist() -> None:
    main_css = (STATIC_DIR / "css" / "main.css").read_text(encoding="utf-8")
    imports = re.findall(r'@import url\("([^"]+)"\)', main_css)

    assert imports
    for path in imports:
        assert (STATIC_DIR / "css" / path).is_file(), path


def test_every_css_file_is_imported() -> None:
    main_css = (STATIC_DIR / "css" / "main.css").read_text(encoding="utf-8")
    imported = set(re.findall(r'@import url\("([^"]+)"\)', main_css))
    css_files = {
        path.relative_to(STATIC_DIR / "css").as_posix()
        for path in (STATIC_DIR / "css").rglob("*.css")
        if path.name != "main.css"
    }

    assert css_files == imported


def test_js_imports_exist() -> None:
    main_js = (STATIC_DIR / "js" / "main.js").read_text(encoding="utf-8")
    imports = re.findall(r'from "\./([^"]+)"', main_js)

    assert imports
    for path in imports:
        assert (STATIC_DIR / "js" / path).is_file(), path


def test_user_color_classes_match_palette() -> None:
    avatar_css = (STATIC_DIR / "css" / "components" / "avatar.css").read_text(encoding="utf-8")
    css_colors = re.findall(r"\.u-color-(\d+) \{ --fm-user-color: (#[0-9a-f]{6}); \}", avatar_css)

    assert [(int(index), hex_value) for index, hex_value in css_colors] == [
        (index, hex_value) for index, (_name, hex_value) in enumerate(USER_COLORS)
    ]


@pytest.mark.parametrize(
    "asset",
    ["css/main.css", "js/main.js", "js/theme-init.js", "vendor/bootstrap/bootstrap.min.css", "img/favicon.svg"],
)
def test_static_assets_are_served(client, asset: str) -> None:
    assert client.get(f"/static/{asset}").status_code == 200


def test_fonts_have_font_mime_type(client) -> None:
    response = client.get("/static/vendor/inter/inter-latin-wght-normal.woff2")

    assert response.mimetype == "font/woff2"
