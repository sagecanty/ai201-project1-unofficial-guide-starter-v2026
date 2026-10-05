"""
Stage 1 of the pipeline: loading documents off disk and cleaning them up.

The five stages are loading, chunking, embedding, retrieval, and generation.
When something goes wrong in unit 2, your job is to work out which of the five
it happened in. This is the first one.
"""

import re
from dataclasses import dataclass
from pathlib import Path

import config


@dataclass
class Document:
    """One source file, cleaned and ready to be chunked."""

    source: str   # the filename, e.g. "housing_lottery.txt" — this is what gets cited
    text: str


def clean_text(raw: str) -> str:
    """
    Strip the stuff that isn't the real content.

    Provided corpora are already fairly clean. If you bring your own documents
    — especially anything scraped from a web page — this is where navigation
    text, ads, cookie banners and repeated boilerplate come out.
    """
    text = raw.replace("\r\n", "\n").replace("\r", "\n")

    # Collapse runs of blank lines down to one.
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Collapse repeated spaces and tabs, but keep line structure intact.
    text = re.sub(r"[ \t]{2,}", " ", text)

    # Undo hard wrapping. Some guides wrap prose at ~80 columns, so one sentence
    # arrives as three lines. Join the lines inside each paragraph, but never
    # glue a markdown heading onto the text under it.
    blocks = []
    for block in text.strip().split("\n\n"):
        lines = [ln.strip() for ln in block.split("\n") if ln.strip()]
        if not lines:
            continue
        if lines[0].startswith("#"):
            head, rest = lines[0], lines[1:]
            blocks.append(head if not rest else head + "\n\n" + " ".join(rest))
        else:
            blocks.append(" ".join(lines))

    return "\n\n".join(blocks).strip()


# A section body that turns up word-for-word in this many documents is a
# template, not information. In city_guides the "Practical notes" paragraph is
# pasted unchanged into all nine town guides, and it is actively wrong for most
# of them: it says "the nearest full hospital is in Brightwater" inside the
# Brightwater guide itself, while guide_accessibility.md says the nearest full
# hospital is in Marchwood. Left in, it gets retrieved nine times over and
# outvotes the one document that is right.
BOILERPLATE_MIN_DOCS = 3

_SECTION_SPLIT = re.compile(r"(?m)^(?=## )")


def _sections(text: str) -> list[str]:
    return [s for s in _SECTION_SPLIT.split(text) if s.strip()]


def _section_body(section: str) -> str:
    lines = section.strip().split("\n", 1)
    body = lines[1] if lines[0].startswith("#") and len(lines) > 1 else section
    return re.sub(r"\s+", " ", body).strip().lower()


def strip_repeated_sections(documents: list["Document"]) -> tuple[list["Document"], int]:
    """
    Drop any `##` section whose body is identical across BOILERPLATE_MIN_DOCS
    or more documents. Returns the cleaned documents and how many sections went.
    """
    from collections import Counter

    seen = Counter()
    for doc in documents:
        for body in {_section_body(s) for s in _sections(doc.text)}:
            seen[body] += 1
    repeated = {b for b, n in seen.items() if n >= BOILERPLATE_MIN_DOCS and b}

    removed = 0
    cleaned: list[Document] = []
    for doc in documents:
        kept = []
        for section in _sections(doc.text):
            if section.lstrip().startswith("## ") and _section_body(section) in repeated:
                removed += 1
                continue
            kept.append(section.strip())
        cleaned.append(Document(source=doc.source, text="\n\n".join(kept)))
    return cleaned, removed


def load_documents(corpus: str | None = None) -> list[Document]:
    """
    Read every .txt and .md file in the corpus folder.

    Returns a list of Documents. Each one keeps its filename, because every
    answer your system produces has to name the document it came from.
    """
    folder = config.corpus_path(corpus)

    if not folder.exists():
        raise FileNotFoundError(
            f"No corpus at {folder}.\n"
            f"Check the corpus name in config.py, or see corpora/README.md "
            f"for what's available."
        )

    documents: list[Document] = []
    for path in sorted(folder.iterdir()):
        if path.suffix.lower() not in {".txt", ".md"}:
            continue
        text = clean_text(path.read_text(encoding="utf-8"))
        if text:
            documents.append(Document(source=path.name, text=text))

    if not documents:
        raise ValueError(f"{folder} has no .txt or .md files in it.")

    documents, _ = strip_repeated_sections(documents)
    return documents


def describe(documents: list[Document]) -> str:
    """A one-line summary, printed after indexing so you can sanity-check it."""
    total = sum(len(d.text) for d in documents)
    avg = total // max(len(documents), 1)
    return (
        f"{len(documents)} documents, "
        f"{total:,} characters, "
        f"~{avg:,} characters per document"
    )


if __name__ == "__main__":
    docs = load_documents()
    print(describe(docs))
    print()
    for doc in docs[:3]:
        preview = doc.text[:200].replace("\n", " ")
        print(f"  {doc.source}: {preview}...")
