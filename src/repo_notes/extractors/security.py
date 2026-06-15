"""Security scanner for secrets and sensitive files."""

from dataclasses import dataclass, field
from pathlib import Path
import re
import math
from repo_notes.scanner import FileInfo
from repo_notes.file_cache import read_text


SECRET_PATTERNS = [
    (r"aws_access_key_id\s*[:=]\s*['\"]?([A-Z0-9]{20})['\"]?", "AWS Access Key"),
    (r"aws_secret_access_key\s*[:=]\s*['\"]?([A-Za-z0-9/+=]{40})['\"]?", "AWS Secret Key"),
    (r"github_pat_[a-zA-Z0-9_]{22,}", "GitHub Personal Access Token"),
    (r"ghp_[a-zA-Z0-9]{36}", "GitHub Token"),
    (r"gho_[a-zA-Z0-9]{36}", "GitHub OAuth Token"),
    (r"ghu_[a-zA-Z0-9]{36}", "GitHub User Token"),
    (r"ghs_[a-zA-Z0-9]{36}", "GitHub Server Token"),
    (r"ghr_[a-zA-Z0-9]{36}", "GitHub Refresh Token"),
    (r"api_key\s*[:=]\s*['\"]?([a-zA-Z0-9_\-]{32,})['\"]?", "Generic API Key"),
    (r"secret_key\s*[:=]\s*['\"]?([a-zA-Z0-9_\-]{32,})['\"]?", "Secret Key"),
    (r"private_key\s*[:=]\s*['\"]?([a-zA-Z0-9_\-]{32,})['\"]?", "Private Key"),
    (r"database_url\s*[:=]\s*['\"]?(postgres|mysql|mongodb)://[^'\"]+['\"]?", "Database URL"),
    (r"redis_url\s*[:=]\s*['\"]?redis://[^'\"]+['\"]?", "Redis URL"),
    (r"jwt_secret\s*[:=]\s*['\"]?([a-zA-Z0-9_\-]{32,})['\"]?", "JWT Secret"),
    (r"-----BEGIN (RSA|EC|DSA|OPENSSH) PRIVATE KEY-----", "Private Key Block"),
    # AI provider API keys
    (r"(?i)sk-proj-[A-Za-z0-9]{20,}", "OpenAI Project Key"),
    (r"(?i)sk-ant-api03-[A-Za-z0-9]{24,}", "Anthropic API Key"),
    (r"AIzaSy[A-Za-z0-9_-]{33}", "Google Gemini API Key"),
    (r"(?i)(?:trial|prod)_[A-Za-z0-9]{20,}", "Cohere API Key"),
    (r"hf_[A-Za-z0-9]{20,}", "Hugging Face API Key"),
    (r"(?i)v[12]\.[A-Za-z0-9]{20,}", "Mistral API Key"),
    (r"gsk_[A-Za-z0-9]{20,}", "Groq API Key"),
    (r"pplx-[A-Za-z0-9]{20,}", "Perplexity API Key"),
    (r"ese_[A-Za-z0-9]{20,}", "Anyscale API Key"),
    (r"r8_[A-Za-z0-9]{20,}", "Replicate API Key"),
    (r"sk-or-v1-[A-Za-z0-9]{20,}", "OpenRouter API Key"),
    (r"(?i)sk-[A-Za-z0-9]{32,}", "Generic AI Secret Key"),
]


@dataclass(slots=True)
class SecurityResult:
    findings: list[dict[str, str]] = field(default_factory=list)
    env_files: list[Path] = field(default_factory=list)
    high_entropy_strings: list[dict[str, str]] = field(default_factory=list)


class SecurityExtractor:
    def __init__(self, entropy_threshold: float = 4.5, patterns: list[str] | None = None):
        self.entropy_threshold = entropy_threshold
        self._compiled_patterns = [(re.compile(p, re.IGNORECASE), name) for p, name in SECRET_PATTERNS]
        if patterns:
            for p in patterns:
                try:
                    self._compiled_patterns.append((re.compile(p, re.IGNORECASE), "Custom Pattern"))
                except re.error:
                    pass

    def extract(self, root: Path, files: list[FileInfo]) -> SecurityResult:
        findings = []
        env_files = []
        high_entropy = []

        for f in files:
            if f.is_binary:
                continue

            rel = f.relative_path

            # Check for .env files
            if rel.name.startswith(".env") or rel.name == "local.settings.json":
                env_files.append(rel)
                continue

            content = self._read_content(f.path)
            if not content:
                continue

            # Pattern-based detection
            for pattern, name in self._compiled_patterns:
                for match in pattern.finditer(content):
                    findings.append({
                        "file": rel.as_posix(),
                        "type": name,
                        "line": self._get_line_number(content, match.start()),
                        "preview": self._redact(match.group(0)),
                    })

            # Entropy-based detection
            for match in re.finditer(r"[a-zA-Z0-9/+=]{20,}", content):
                entropy = self._shannon_entropy(match.group(0))
                if entropy >= self.entropy_threshold:
                    high_entropy.append({
                        "file": rel.as_posix(),
                        "entropy": round(entropy, 2),
                        "line": self._get_line_number(content, match.start()),
                        "preview": self._redact(match.group(0)[:50]),
                    })

        return SecurityResult(
            findings=findings,
            env_files=env_files,
            high_entropy_strings=high_entropy[:50],  # Limit output
        )

    def _read_content(self, path: Path) -> str:
        return read_text(path)

    def _get_line_number(self, content: str, pos: int) -> int:
        return content[:pos].count("\n") + 1

    def _redact(self, value: str) -> str:
        if len(value) <= 8:
            return "*" * len(value)
        return value[:4] + "*" * (len(value) - 8) + value[-4:]

    def _shannon_entropy(self, data: str) -> float:
        if not data:
            return 0.0
        freq = {}
        for c in data:
            freq[c] = freq.get(c, 0) + 1
        entropy = 0.0
        n = len(data)
        for count in freq.values():
            p = count / n
            entropy -= p * math.log2(p)
        return entropy