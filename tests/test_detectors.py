"""Tests for detector modules."""

from pathlib import Path

from repo_notes.detectors.go import GO_INFO, GoDetector
from repo_notes.detectors.javascript import JS_INFO, JavaScriptDetector
from repo_notes.detectors.python import PYTHON_INFO, PythonDetector
from repo_notes.detectors.registry import DetectorRegistry, get_registry
from repo_notes.detectors.rust import RUST_INFO, RustDetector


class TestPythonDetector:
    def test_classifies_py(self):
        detector = PythonDetector()
        result = detector.classify(Path("main.py"))
        assert result == PYTHON_INFO

    def test_classifies_pyi(self):
        detector = PythonDetector()
        result = detector.classify(Path("types.pyi"))
        assert result == PYTHON_INFO

    def test_rejects_non_python(self):
        detector = PythonDetector()
        result = detector.classify(Path("main.js"))
        assert result is None


class TestJavaScriptDetector:
    def test_classifies_js(self):
        detector = JavaScriptDetector()
        result = detector.classify(Path("app.js"))
        assert result == JS_INFO

    def test_rejects_py(self):
        detector = JavaScriptDetector()
        result = detector.classify(Path("main.py"))
        assert result is None


class TestGoDetector:
    def test_classifies_go(self):
        detector = GoDetector()
        result = detector.classify(Path("main.go"))
        assert result == GO_INFO

    def test_rejects_rs(self):
        detector = GoDetector()
        result = detector.classify(Path("main.rs"))
        assert result is None


class TestRustDetector:
    def test_classifies_rs(self):
        detector = RustDetector()
        result = detector.classify(Path("main.rs"))
        assert result == RUST_INFO

    def test_does_not_classify_toml(self):
        detector = RustDetector()
        result = detector.classify(Path("pyproject.toml"))
        assert result is None


class TestRegistry:
    def test_register_and_get(self):
        registry = DetectorRegistry()
        detector = PythonDetector()
        registry.register(detector)
        assert registry.get_for_extension(".py") is detector

    def test_classify_by_extension(self):
        registry = DetectorRegistry()
        registry.register(PythonDetector())
        result = registry.classify(Path("main.py"))
        assert result == PYTHON_INFO

    def test_classify_unknown(self):
        registry = DetectorRegistry()
        registry.register(PythonDetector())
        result = registry.classify(Path("main.xyz"))
        assert result is None

    def test_get_enabled_filters(self):
        registry = DetectorRegistry()
        registry.register(PythonDetector())
        registry.register(JavaScriptDetector())
        filtered = registry.get_enabled(["python"])
        assert filtered.get_for_extension(".py") is not None
        assert filtered.get_for_extension(".js") is None

    def test_get_enabled_all(self):
        registry = DetectorRegistry()
        registry.register(PythonDetector())
        filtered = registry.get_enabled(["all"])
        assert filtered.get_for_extension(".py") is not None

    def test_global_registry(self):
        registry = get_registry()
        assert registry.get_for_extension(".py") is not None
        assert registry.get_for_extension(".js") is not None
        assert registry.get_for_extension(".go") is not None
        assert registry.get_for_extension(".rs") is not None
        # .toml should NOT be mapped to rust
        assert registry.get_for_extension(".toml") is None
