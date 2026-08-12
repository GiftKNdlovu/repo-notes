"""Tests for data-driven language classification registry."""

from pathlib import Path

import pytest

from repo_notes.detectors import (
    C_CPP_INFO,
    DOCKER_INFO,
    GO_INFO,
    JAVA_INFO,
    JS_INFO,
    KOTLIN_INFO,
    PHP_INFO,
    PYTHON_INFO,
    R_LANG_INFO,
    RUBY_INFO,
    RUST_INFO,
    SHELL_INFO,
    SQL_INFO,
    SWIFT_INFO,
    TS_INFO,
    DetectorRegistry,
    LanguageInfo,
    get_registry,
)


@pytest.mark.parametrize(
    "file_path, expected_info",
    [
        ("main.py", PYTHON_INFO),
        ("types.pyi", PYTHON_INFO),
        ("app.js", JS_INFO),
        ("app.jsx", JS_INFO),
        ("app.ts", TS_INFO),
        ("app.tsx", TS_INFO),
        ("main.go", GO_INFO),
        ("main.rs", RUST_INFO),
        ("Main.java", JAVA_INFO),
        ("main.c", C_CPP_INFO),
        ("main.cpp", C_CPP_INFO),
        ("main.hpp", C_CPP_INFO),
        ("app.rb", RUBY_INFO),
        ("index.php", PHP_INFO),
        ("App.swift", SWIFT_INFO),
        ("App.kt", KOTLIN_INFO),
        ("script.r", R_LANG_INFO),
        ("report.rmd", R_LANG_INFO),
        ("script.sh", SHELL_INFO),
        ("script.bash", SHELL_INFO),
        ("query.sql", SQL_INFO),
        ("Dockerfile", DOCKER_INFO),
        ("docker-compose.yml", DOCKER_INFO),
        ("app.Dockerfile", DOCKER_INFO),
    ],
)
def test_global_registry_classification(file_path, expected_info):
    registry = get_registry()
    assert registry.classify(Path(file_path)) == expected_info


def test_classify_unknown():
    registry = get_registry()
    assert registry.classify(Path("main.xyz")) is None
    assert registry.get_for_extension(".toml") is None


def test_custom_registration():
    registry = DetectorRegistry()
    custom_info = LanguageInfo("zig", "systems", frozenset({".zig"}))
    registry.register(custom_info)
    assert registry.get_for_extension(".zig") == custom_info
    assert registry.classify(Path("main.zig")) == custom_info


def test_get_enabled_filters():
    registry = DetectorRegistry()
    registry.register(PYTHON_INFO)
    registry.register(JS_INFO)
    filtered = registry.get_enabled(["python"])
    assert filtered.get_for_extension(".py") == PYTHON_INFO
    assert filtered.get_for_extension(".js") is None


def test_get_enabled_all():
    registry = DetectorRegistry()
    registry.register(PYTHON_INFO)
    filtered = registry.get_enabled(["all"])
    assert filtered.get_for_extension(".py") == PYTHON_INFO
