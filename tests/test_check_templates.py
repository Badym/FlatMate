from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("check_templates", PROJECT_ROOT / "scripts" / "check_templates.py")
assert _spec and _spec.loader
check_templates = importlib.util.module_from_spec(_spec)
sys.modules["check_templates"] = check_templates
_spec.loader.exec_module(check_templates)


def _project_with_template(tmp_path: Path, content: str) -> Path:
    templates = tmp_path / "app" / "templates"
    templates.mkdir(parents=True)
    (templates / "page.html").write_text(content, encoding="utf-8")
    return tmp_path


def test_project_templates_are_clean() -> None:
    assert check_templates.find_violations(PROJECT_ROOT) == []


@pytest.mark.parametrize(
    "snippet",
    [
        "{{ user.name|safe }}",
        "<script>alert(1)</script>",
        '<button onclick="go()">x</button>',
        '<div style="color: red">x</div>',
        '<a href="javascript:void(0)">x</a>',
    ],
)
def test_detects_unsafe_template_constructs(tmp_path: Path, snippet: str) -> None:
    root = _project_with_template(tmp_path, snippet)

    assert len(check_templates.find_violations(root)) == 1


def test_allows_external_scripts(tmp_path: Path) -> None:
    root = _project_with_template(tmp_path, '<script src="/static/js/app.js"></script>')

    assert check_templates.find_violations(root) == []


def test_detects_markup_in_python(tmp_path: Path) -> None:
    root = _project_with_template(tmp_path, "<p>ok</p>")
    (root / "app" / "view.py").write_text("html = Markup(value)\n", encoding="utf-8")

    violations = check_templates.find_violations(root)

    assert [v.message for v in violations] == ["Markup() wyłącza escapowanie"]


def test_main_exit_codes(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    clean = _project_with_template(tmp_path / "clean", "<p>ok</p>")
    dirty = _project_with_template(tmp_path / "dirty", "{{ x|safe }}")

    assert check_templates.main(["check", str(clean)]) == 0
    assert check_templates.main(["check", str(dirty)]) == 1
    assert "page.html:1" in capsys.readouterr().out
