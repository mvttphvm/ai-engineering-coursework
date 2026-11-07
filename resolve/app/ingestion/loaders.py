"""Document loaders for .md / .txt / .html files.

Real-world KBs are messy, so loading includes a cleaning pass: HTML is
reduced to text, markdown control characters are normalized, whitespace is
collapsed, and exact-duplicate documents are dropped by content hash.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path

SUPPORTED_SUFFIXES = {".md", ".txt", ".html", ".htm"}


@dataclass
class LoadedDocument:
    source: str          # e.g. "password-reset.md" — used as the citation id
    title: str
    text: str
    metadata: dict = field(default_factory=dict)

    @property
    def content_hash(self) -> str:
        return hashlib.sha256(self.text.encode("utf-8")).hexdigest()


class _TextExtractor(HTMLParser):
    """Minimal HTML -> text: keep text nodes, break lines on block tags."""

    _BLOCK = {"p", "div", "br", "li", "h1", "h2", "h3", "h4", "tr"}

    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self._skip = False

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style"}:
            self._skip = True
        if tag in self._BLOCK:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in {"script", "style"}:
            self._skip = False
        if tag in self._BLOCK:
            self.parts.append("\n")

    def handle_data(self, data):
        if not self._skip:
            self.parts.append(data)


def clean_text(raw: str) -> str:
    """Normalize whitespace and strip markdown noise without losing meaning."""
    text = raw.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Strip zero-width and BOM characters that sneak in from exports.
    text = text.replace("﻿", "").replace("​", "")
    return text.strip()


def html_to_text(raw: str) -> str:
    parser = _TextExtractor()
    parser.feed(raw)
    return clean_text("".join(parser.parts))


def _title_from(text: str, fallback: str) -> str:
    for line in text.splitlines():
        line = line.strip().lstrip("#").strip()
        if line:
            return line[:120]
    return fallback


def load_file(path: Path) -> LoadedDocument:
    raw = path.read_text(encoding="utf-8", errors="replace")
    if path.suffix.lower() in {".html", ".htm"}:
        text = html_to_text(raw)
    else:
        text = clean_text(raw)
    return LoadedDocument(
        source=path.name,
        title=_title_from(text, path.stem),
        text=text,
        metadata={"path": str(path)},
    )


def load_directory(directory: str | Path) -> list[LoadedDocument]:
    """Load every supported file in a directory, de-duplicated by content."""
    root = Path(directory)
    if not root.exists():
        raise FileNotFoundError(f"Ingest directory not found: {root}")
    docs: list[LoadedDocument] = []
    seen_hashes: set[str] = set()
    for path in sorted(root.iterdir()):
        if path.is_file() and path.suffix.lower() in SUPPORTED_SUFFIXES:
            doc = load_file(path)
            if doc.text and doc.content_hash not in seen_hashes:
                seen_hashes.add(doc.content_hash)
                docs.append(doc)
    return docs
