from __future__ import annotations

import ntpath
import posixpath
from types import ModuleType

import pytest
from markupsafe import escape
from markupsafe import Markup

from flask_debugtoolbar.utils import _relative_paths
from flask_debugtoolbar.utils import _shortest_relative_path
from flask_debugtoolbar.utils import decode_text
from flask_debugtoolbar.utils import format_sql
from flask_debugtoolbar.utils import HAVE_PYGMENTS


@pytest.mark.parametrize(
    "value,paths,expected,path_module",
    [
        # should yield relative path to the parent directory
        ("/foo/bar", ["/foo"], ["bar"], posixpath),
        ("c:\\foo\\bar", ["c:\\foo"], ["bar"], ntpath),
        # should not yield result if no path is a parent directory
        ("/foo/bar", ["/baz"], [], posixpath),
        ("c:\\foo\\bar", ["c:\\baz"], [], ntpath),
        # should only yield relative paths for parent directories
        ("/foo/bar", ["/foo", "/baz"], ["bar"], posixpath),
        ("c:\\foo\\bar", ["c:\\foo", "c:\\baz"], ["bar"], ntpath),
        # should yield all results when multiple parents match
        ("/foo/bar/baz", ["/foo", "/foo/bar"], ["bar/baz", "baz"], posixpath),
        ("c:\\foo\\bar\\baz", ["c:\\foo", "c:\\foo\\bar"], ["bar\\baz", "baz"], ntpath),
        # should ignore case differences on windows
        ("c:\\Foo\\bar", ["c:\\foo"], ["bar"], ntpath),
        # should preserve original case
        ("/Foo/Bar", ["/Foo"], ["Bar"], posixpath),
        ("c:\\Foo\\Bar", ["c:\\foo"], ["Bar"], ntpath),
    ],
)
def test_relative_paths(
    value: str, paths: list[str], expected: list[str], path_module: ModuleType
) -> None:
    assert list(_relative_paths(value, paths, path_module)) == expected


@pytest.mark.parametrize(
    "value,paths,expected,path_module",
    [
        # should yield relative path to the parent directory
        ("/foo/bar", ["/foo"], "bar", posixpath),
        ("c:\\foo\\bar", ["c:\\foo"], "bar", ntpath),
        # should return the original value if no path is a parent directory
        ("/foo/bar", ["/baz"], "/foo/bar", posixpath),
        ("c:\\foo\\bar", ["c:\\baz"], "c:\\foo\\bar", ntpath),
        # should yield shortest result when multiple parents match
        ("/foo/bar/baz", ["/foo", "/foo/bar"], "baz", posixpath),
        ("c:\\foo\\bar\\baz", ["c:\\foo", "c:\\foo\\bar"], "baz", ntpath),
    ],
)
def test_shortest_relative_path(
    value: str, paths: list[str], expected: str, path_module: ModuleType
) -> None:
    assert _shortest_relative_path(value, paths, path_module) == expected


def test_decode_text_unicode() -> None:
    value = "\uffff"
    decoded = decode_text(value)
    assert decoded == value


def test_decode_text_ascii() -> None:
    value = "abc"
    assert decode_text(value.encode("ascii")) == value


def test_decode_text_non_ascii() -> None:
    value = b"abc \xff xyz"
    assert isinstance(value, bytes)

    decoded = decode_text(value)
    assert not isinstance(decoded, bytes)

    assert decoded.startswith("abc")
    assert decoded.endswith("xyz")


@pytest.fixture()
def no_pygments(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("flask_debugtoolbar.utils.HAVE_PYGMENTS", False)


@pytest.mark.usefixtures("no_pygments")
def test_format_sql_no_pygments() -> None:
    sql = "select 1"
    assert format_sql(sql, {}) == sql


@pytest.mark.usefixtures("no_pygments")
def test_format_sql_no_pygments_non_ascii() -> None:
    sql = b"select '\xff'"
    formatted = format_sql(sql, {})
    assert formatted.startswith("select '")


@pytest.mark.usefixtures("no_pygments")
def test_format_sql_no_pygments_escape_html() -> None:
    sql = "select x < 1"
    formatted = format_sql(sql, {})
    assert not isinstance(formatted, Markup)
    assert escape(formatted) == "select x &lt; 1"


@pytest.mark.skipif(not HAVE_PYGMENTS, reason='test requires the "Pygments" library')
def test_format_sql_pygments() -> None:
    sql = "select 1"
    html = format_sql(sql, {})
    assert isinstance(html, Markup)
    assert html.startswith("<div")
    assert "select" in html
    assert "1" in html


@pytest.mark.skipif(not HAVE_PYGMENTS, reason='test requires the "Pygments" library')
def test_format_sql_pygments_non_ascii() -> None:
    sql = b"select 'abc \xff xyz'"
    html = format_sql(sql, {})
    assert isinstance(html, Markup)
    assert html.startswith("<div")
    assert "select" in html
    assert "abc" in html
    assert "xyz" in html
