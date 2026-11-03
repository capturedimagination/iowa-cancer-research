#!/usr/bin/env python3
"""Read-only publication checks against Git's index, never untracked archives.

Usage: python3 scripts/check_publication.py [--root REPOSITORY]
       [--manifest EXPECTED_FILES.json]

An optional JSON manifest is a list of repository-relative paths, or an object
with a ``files`` list. Entries may be strings or objects with ``path``/``file``.
It must describe the complete indexed file set. Findings contain only the file,
line number when applicable, and category; matched content is never printed.
These bounded checks do not constitute a complete security or licensing audit.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
import os
from pathlib import Path, PurePosixPath
import posixpath
import re
import subprocess
import sys
from urllib.parse import unquote, urlsplit


MAX_BLOB_BYTES = 100_000_000
TEXT_SUFFIXES = {
    ".md", ".markdown", ".txt", ".json", ".jsonl", ".csv", ".tsv",
    ".py", ".swift", ".r", ".rmd", ".html", ".htm", ".xml", ".yaml",
    ".yml", ".toml", ".ini", ".cfg", ".sh", ".bash", ".zsh", ".sql",
    ".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx", ".css", ".svg",
}
BINARY_SUFFIXES = {
    ".pdf", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".mp4",
    ".mp3", ".wav", ".npy", ".npz", ".xlsx", ".xls", ".docx", ".pptx",
    ".zip", ".gz", ".bz2", ".xz", ".7z", ".tar", ".woff", ".woff2",
    ".ttf", ".otf",
}
PRIVATE_COMPONENTS = {
    ".publication", "__pycache__", ".cache", "cache", ".pytest_cache", ".mypy_cache",
    ".ruff_cache", ".venv", "venv", "node_modules", ".ssh", ".git",
    "private", "secrets",
}

# Pattern syntax deliberately avoids embedding an example credential or account
# path. Public contributor email addresses are not secret-token patterns.
CONTENT_PATTERNS = (
    ("private_key", re.compile(
        r"-----BEGIN (?:RSA |EC |OPENSSH |DSA |ENCRYPTED )?PRIVATE KEY-----")),
    ("github_token", re.compile(
        r"(?<![A-Za-z0-9_])(?:gh[pousr]_[A-Za-z0-9]{25,}|"
        r"github_pat_[A-Za-z0-9_]{30,})(?![A-Za-z0-9_])")),
    ("service_token", re.compile(
        r"(?<![A-Za-z0-9_])(?:sk-(?:proj-|svcacct-)?[A-Za-z0-9_-]{25,}|"
        r"xox[baprs]-[A-Za-z0-9-]{20,}|AKIA[A-Z0-9]{16})(?![A-Za-z0-9_])")),
    ("credential_assignment", re.compile(
        r"(?i)\b(?:api[_-]?key|access[_-]?token|refresh[_-]?token|"
        r"auth[_-]?token|password|client[_-]?secret)\b[\"']?\s*[=:]\s*"
        r"[\"'][A-Za-z0-9_./+\-=]{8,}[\"']")),
    ("signed_download_url", re.compile(
        r"(?i)\bX-Amz-(?:Credential|Signature)(?:=|%3d)")),
    ("local_account_path", re.compile(
        r"(?:/" "Users/" r"[^/\s\"'<>]+|(?i:[A-Z]:\\{1,2}"
        r"Users\\{1,2}[^\\\s\"'<>]+))")),
)


@dataclass(frozen=True, order=True)
class Finding:
    path: str
    line: int
    category: str


@dataclass(frozen=True)
class IndexEntry:
    path: str
    oid: str
    mode: str
    stage: str


class CheckError(Exception):
    """An operational failure, represented without potentially sensitive output."""


def git(root: Path, *args: str, input_data: bytes | None = None) -> bytes:
    env = {**os.environ, "GIT_OPTIONAL_LOCKS": "0"}
    try:
        result = subprocess.run(
            ["git", "-C", str(root), *args], input=input_data,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False, env=env,
        )
    except OSError as exc:
        raise CheckError("git_unavailable") from exc
    if result.returncode:
        raise CheckError("git_read_failed")
    return result.stdout


def index_entries(root: Path) -> list[IndexEntry]:
    entries = []
    raw = git(root, "ls-files", "--cached", "--stage", "-z")
    for item in raw.split(b"\0"):
        if not item:
            continue
        try:
            metadata, raw_path = item.split(b"\t", 1)
            mode, oid, stage = metadata.decode("ascii").split()
            path = raw_path.decode("utf-8", errors="surrogateescape")
        except (ValueError, UnicodeError) as exc:
            raise CheckError("invalid_index_record") from exc
        entries.append(IndexEntry(path, oid, mode, stage))
    return entries


def blob_sizes(root: Path, entries: list[IndexEntry]) -> dict[str, int]:
    oids = sorted({entry.oid for entry in entries if entry.mode != "160000"})
    if not oids:
        return {}
    raw = git(root, "cat-file", "--batch-check", input_data=("\n".join(oids) + "\n").encode())
    sizes = {}
    for record in raw.splitlines():
        try:
            oid, kind, size = record.decode("ascii").split()
            if kind != "blob":
                raise ValueError("not a blob")
            sizes[oid] = int(size)
        except (ValueError, UnicodeError) as exc:
            raise CheckError("unreadable_index_blob") from exc
    if set(sizes) != set(oids):
        raise CheckError("incomplete_index_metadata")
    return sizes


def path_categories(path: str) -> list[str]:
    p = PurePosixPath(path)
    parts = {part.casefold() for part in p.parts}
    categories = []
    if parts & PRIVATE_COMPONENTS or p.name == ".DS_Store":
        categories.append("private_or_cache_path")
    if p.suffix.casefold() in {".sqlite", ".sqlite3", ".db", ".db3"}:
        categories.append("sqlite_or_database_blob")
    if p.suffix.casefold() in {".pyc", ".pyo"}:
        categories.append("compiled_python_cache")
    name = p.name.casefold()
    if name in {".env", "id_rsa", "id_ed25519", "credentials", "credentials.json"} or (
        name.startswith(".env.") and name not in {".env.example", ".env.sample", ".env.template"}
    ):
        categories.append("credential_file_path")
    return categories


def decode_text(path: str, data: bytes) -> str | None:
    suffix = PurePosixPath(path).suffix.casefold()
    if suffix in BINARY_SUFFIXES:
        return None
    if suffix not in TEXT_SUFFIXES and b"\0" in data[:8192]:
        return None
    return data.decode("utf-8-sig", errors="replace")


def content_findings(path: str, text: str) -> list[Finding]:
    findings = []
    for line_number, line in enumerate(text.splitlines(), 1):
        for category, pattern in CONTENT_PATTERNS:
            if pattern.search(line):
                findings.append(Finding(path, line_number, category))
    return findings


def mask_markdown_code(text: str) -> str:
    """Mask code while preserving line numbers for publication-link checks."""
    lines = text.splitlines(keepends=True)
    fence = None
    output = []
    for line in lines:
        opening = re.match(r"^\s{0,3}(`{3,}|~{3,})", line)
        if fence:
            output.append(re.sub(r"[^\r\n]", " ", line))
            if opening and opening.group(1)[0] == fence[0] and len(opening.group(1)) >= len(fence):
                fence = None
        elif opening:
            fence = opening.group(1)
            output.append(re.sub(r"[^\r\n]", " ", line))
        else:
            output.append(line)
    masked = "".join(output)
    return re.sub(r"(`+)(.*?)\1", lambda m: re.sub(r"[^\r\n]", " ", m.group()), masked, flags=re.S)


def inline_destination(text: str, start: int) -> str | None:
    """Read a Markdown destination, including balanced or escaped parentheses."""
    i = start
    while i < len(text) and text[i].isspace():
        i += 1
    if i >= len(text):
        return None
    if text[i] == "<":
        end = text.find(">", i + 1)
        return text[i + 1:end] if end != -1 else None
    begin, depth = i, 0
    while i < len(text):
        char = text[i]
        if char == "\\" and i + 1 < len(text):
            i += 2
            continue
        if char == "(":
            depth += 1
        elif char == ")":
            if depth == 0:
                return text[begin:i]
            depth -= 1
        elif char.isspace() and depth == 0:
            return text[begin:i]
        i += 1
    return None


def markdown_links(text: str) -> list[tuple[int, str]]:
    masked = mask_markdown_code(text)
    links = []
    for match in re.finditer(r"!?\[[^\]\n]*\]\(\s*", masked):
        destination = inline_destination(masked, match.end())
        if destination is not None:
            links.append((masked.count("\n", 0, match.start()) + 1, destination))
    for match in re.finditer(r"^\s{0,3}\[[^\]\n]+\]:\s*(<[^>\n]*>|\S+)", masked, re.M):
        links.append((masked.count("\n", 0, match.start()) + 1, match.group(1).strip("<>")))
    return links


def markdown_findings(path: str, text: str, indexed_paths: set[str]) -> list[Finding]:
    findings = []
    for line, destination in markdown_links(text):
        destination = re.sub(r"\\([\\`*{}\[\]()#+.! _-])", r"\1", destination)
        try:
            parsed = urlsplit(destination)
        except ValueError:
            findings.append(Finding(path, line, "invalid_markdown_target"))
            continue
        if parsed.scheme or parsed.netloc or not parsed.path:
            continue
        target_path = unquote(parsed.path)
        target = posixpath.normpath(
            target_path.lstrip("/") if target_path.startswith("/")
            else posixpath.join(posixpath.dirname(path), target_path)
        )
        if target == ".." or target.startswith("../"):
            findings.append(Finding(path, line, "markdown_target_outside_index"))
        elif target not in indexed_paths and target != "." and not any(
            candidate.startswith(target.rstrip("/") + "/") for candidate in indexed_paths
        ):
            findings.append(Finding(path, line, "missing_markdown_target"))
    return findings


def manifest_findings(manifest: Path, indexed_paths: set[str]) -> list[Finding]:
    try:
        payload = json.loads(manifest.read_text())
        records = payload.get("expected_public_files", payload.get("files")) if isinstance(payload, dict) else payload
        if not isinstance(records, list):
            raise ValueError("not a file list")
        expected = set()
        for record in records:
            path = record.get("path", record.get("file")) if isinstance(record, dict) else record
            if not isinstance(path, str) or not path or path.startswith("/") or ".." in PurePosixPath(path).parts:
                raise ValueError("invalid manifest path")
            expected.add(path.removeprefix("./"))
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise CheckError("invalid_expected_files_manifest") from exc
    return (
        [Finding(path, 0, "manifest_file_not_indexed") for path in expected - indexed_paths]
        + [Finding(path, 0, "indexed_file_missing_from_manifest") for path in indexed_paths - expected]
    )


def check(root: Path, manifest: Path | None = None) -> tuple[list[Finding], int]:
    entries = index_entries(root)
    indexed_paths = {entry.path for entry in entries}
    findings = []
    if not entries:
        findings.append(Finding(".", 0, "empty_publication_index"))
    sizes = blob_sizes(root, entries)
    for entry in entries:
        findings.extend(Finding(entry.path, 0, category) for category in path_categories(entry.path))
        if entry.stage != "0":
            findings.append(Finding(entry.path, 0, "unmerged_index_entry"))
            continue
        if entry.mode not in {"100644", "100755"}:
            findings.append(Finding(entry.path, 0, "unsupported_index_entry"))
            continue
        if sizes[entry.oid] >= MAX_BLOB_BYTES:
            findings.append(Finding(entry.path, 0, "blob_at_or_above_100mb"))
            continue
        if path_categories(entry.path):
            continue
        if PurePosixPath(entry.path).suffix.casefold() in BINARY_SUFFIXES:
            continue
        text = decode_text(entry.path, git(root, "cat-file", "blob", entry.oid))
        if text is None:
            continue
        findings.extend(content_findings(entry.path, text))
        if PurePosixPath(entry.path).suffix.casefold() in {".md", ".markdown"}:
            findings.extend(markdown_findings(entry.path, text, indexed_paths))
    if manifest is not None:
        findings.extend(manifest_findings(manifest, indexed_paths))
    return sorted(set(findings)), len(indexed_paths)


def display_path(path: str) -> str:
    # A control character in a tracked filename cannot inject another log line.
    return path.encode("unicode_escape", errors="backslashreplace").decode("ascii")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", type=Path, help="repository location; defaults to the current repository root")
    parser.add_argument("--manifest", type=Path, help="optional complete expected-file JSON manifest")
    args = parser.parse_args(argv)
    try:
        location = args.root or Path.cwd()
        root = Path(os.fsdecode(git(location, "rev-parse", "--show-toplevel")).strip())
        findings, count = check(root, args.manifest)
    except CheckError as exc:
        print(f".:{exc}", file=sys.stderr)
        return 2
    for finding in findings:
        line = f":{finding.line}" if finding.line else ""
        print(f"{display_path(finding.path)}{line}:{finding.category}")
    if findings:
        print(f"FAIL: {len(findings)} findings in {count} indexed paths.")
        return 1
    print(f"PASS: {count} indexed paths checked; no untracked files scanned.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
