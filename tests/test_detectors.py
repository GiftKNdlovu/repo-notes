"""Tests for detector modules."""

from pathlib import Path

from repo_notes.detectors.c_cpp import C_CPP_INFO, CppDetector
from repo_notes.detectors.docker import DOCKER_INFO, DockerDetector
from repo_notes.detectors.go import GO_INFO, GoDetector
from repo_notes.detectors.java import JAVA_INFO, JavaDetector
from repo_notes.detectors.javascript import JS_INFO, TS_INFO, JavaScriptDetector, TypeScriptDetector
from repo_notes.detectors.kotlin import KOTLIN_INFO, KotlinDetector
from repo_notes.detectors.php import PHP_INFO, PhpDetector
from repo_notes.detectors.python import PYTHON_INFO, PythonDetector
from repo_notes.detectors.r_lang import R_LANG_INFO, RDetector
from repo_notes.detectors.registry import DetectorRegistry, get_registry
from repo_notes.detectors.ruby import RUBY_INFO, RubyDetector
from repo_notes.detectors.rust import RUST_INFO, RustDetector
from repo_notes.detectors.shell import SHELL_INFO, ShellDetector
from repo_notes.detectors.sql import SQL_INFO, SqlDetector
from repo_notes.detectors.swift import SWIFT_INFO, SwiftDetector


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


class TestTypeScriptDetector:
    def test_classifies_ts(self):
        detector = TypeScriptDetector()
        assert detector.classify(Path("app.ts")) == TS_INFO
        assert detector.classify(Path("app.tsx")) == TS_INFO

    def test_rejects_non_ts(self):
        detector = TypeScriptDetector()
        result = detector.classify(Path("main.js"))
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
        assert registry.get_for_extension(".java") is not None
        assert registry.get_for_extension(".rb") is not None
        assert registry.get_for_extension(".php") is not None
        assert registry.get_for_extension(".swift") is not None
        assert registry.get_for_extension(".kt") is not None
        assert registry.get_for_extension(".sh") is not None
        assert registry.get_for_extension(".sql") is not None
        # .toml should NOT be mapped to anything
        assert registry.get_for_extension(".toml") is None


class TestJavaDetector:
    def test_classifies_java(self):
        detector = JavaDetector()
        result = detector.classify(Path("Main.java"))
        assert result == JAVA_INFO

    def test_rejects_non_java(self):
        detector = JavaDetector()
        result = detector.classify(Path("main.py"))
        assert result is None


class TestCppDetector:
    def test_classifies_c(self):
        detector = CppDetector()
        assert detector.classify(Path("main.c")) == C_CPP_INFO
        assert detector.classify(Path("main.h")) == C_CPP_INFO
        assert detector.classify(Path("main.cpp")) == C_CPP_INFO
        assert detector.classify(Path("main.hpp")) == C_CPP_INFO
        assert detector.classify(Path("main.cc")) == C_CPP_INFO
        assert detector.classify(Path("main.cxx")) == C_CPP_INFO

    def test_rejects_non_cpp(self):
        detector = CppDetector()
        result = detector.classify(Path("main.py"))
        assert result is None


class TestRubyDetector:
    def test_classifies_rb(self):
        detector = RubyDetector()
        result = detector.classify(Path("app.rb"))
        assert result == RUBY_INFO

    def test_rejects_non_ruby(self):
        detector = RubyDetector()
        result = detector.classify(Path("main.py"))
        assert result is None


class TestPhpDetector:
    def test_classifies_php(self):
        detector = PhpDetector()
        result = detector.classify(Path("index.php"))
        assert result == PHP_INFO

    def test_rejects_non_php(self):
        detector = PhpDetector()
        result = detector.classify(Path("main.py"))
        assert result is None


class TestSwiftDetector:
    def test_classifies_swift(self):
        detector = SwiftDetector()
        result = detector.classify(Path("App.swift"))
        assert result == SWIFT_INFO

    def test_rejects_non_swift(self):
        detector = SwiftDetector()
        result = detector.classify(Path("main.py"))
        assert result is None


class TestKotlinDetector:
    def test_classifies_kt(self):
        detector = KotlinDetector()
        assert detector.classify(Path("App.kt")) == KOTLIN_INFO
        assert detector.classify(Path("App.kts")) == KOTLIN_INFO

    def test_rejects_non_kotlin(self):
        detector = KotlinDetector()
        result = detector.classify(Path("main.py"))
        assert result is None


class TestRDetector:
    def test_classifies_r(self):
        detector = RDetector()
        assert detector.classify(Path("script.r")) == R_LANG_INFO
        assert detector.classify(Path("report.rmd")) == R_LANG_INFO

    def test_rejects_non_r(self):
        detector = RDetector()
        result = detector.classify(Path("main.py"))
        assert result is None


class TestShellDetector:
    def test_classifies_sh(self):
        detector = ShellDetector()
        assert detector.classify(Path("script.sh")) == SHELL_INFO
        assert detector.classify(Path("script.bash")) == SHELL_INFO
        assert detector.classify(Path("script.zsh")) == SHELL_INFO
        assert detector.classify(Path("script.ps1")) == SHELL_INFO

    def test_rejects_non_shell(self):
        detector = ShellDetector()
        result = detector.classify(Path("main.py"))
        assert result is None


class TestSqlDetector:
    def test_classifies_sql(self):
        detector = SqlDetector()
        result = detector.classify(Path("query.sql"))
        assert result == SQL_INFO

    def test_rejects_non_sql(self):
        detector = SqlDetector()
        result = detector.classify(Path("main.py"))
        assert result is None


class TestDockerDetector:
    def test_classifies_dockerfile(self):
        detector = DockerDetector()
        result = detector.classify(Path("Dockerfile"))
        assert result == DOCKER_INFO

    def test_classifies_docker_compose(self):
        detector = DockerDetector()
        assert detector.classify(Path("docker-compose.yml")) == DOCKER_INFO

    def test_classifies_dockerfile_extension(self):
        detector = DockerDetector()
        assert detector.classify(Path("app.Dockerfile")) == DOCKER_INFO

    def test_rejects_non_docker(self):
        detector = DockerDetector()
        result = detector.classify(Path("main.py"))
        assert result is None
