"""
Stage 2 of the pipeline: splitting documents into chunks.

⚠️ THIS IS THE FILE YOU CHANGE IN MILESTONE 3.

`split_documents` below is deliberately plain. It cuts every document into
fixed-size pieces with a fixed overlap and pays no attention to where sentences
or paragraphs end. It works, and it is not good.

On a corpus of short posts it may not cut anything at all: `campus_life` comes
out as 88 documents and 88 chunks, because almost nothing in it reaches 800
characters. That is the baseline, not a bug — Milestone 3 is where you decide
whether one post should stay one chunk.

Your job in Milestone 3 is to replace the *body* of `split_documents` with a
strategy that fits the documents you actually read in Milestone 1. Keep the
name and the shape of what it returns — the rest of the pipeline calls it, and
your README has to name the function that produced your chunks.

If you get stuck for 30 minutes, `fallback_split` is the original. Switch back
to it, write down what you saw, and move on. That's a real observation about
your pipeline, not giving up.
"""

from dataclasses import dataclass

import config
from ingest import Document


@dataclass
class Chunk:
    """One piece of one document."""

    text: str
    source: str        # which file it came from
    index: int         # which chunk within that file, starting at 0
    produced_by: str   # the function that made it — cite this in your README

    @property
    def label(self) -> str:
        return f"{self.source}#{self.index}"


def fallback_split(
    documents: list[Document],
    chunk_size: int | None = None,
    overlap: int | None = None,
) -> list[Chunk]:
    """
    The starter's original chunker. Fixed-size character windows with overlap.

    Keep this function. Milestone 3's stop rule points back at it, and having
    something to compare your own strategy against is useful in unit 2.
    """
    chunk_size = chunk_size or config.CHUNK_SIZE
    overlap = overlap or config.CHUNK_OVERLAP

    if overlap >= chunk_size:
        raise ValueError("overlap has to be smaller than chunk_size")

    chunks: list[Chunk] = []
    for doc in documents:
        start = 0
        index = 0
        while start < len(doc.text):
            piece = doc.text[start : start + chunk_size].strip()
            if piece:
                chunks.append(
                    Chunk(
                        text=piece,
                        source=doc.source,
                        index=index,
                        produced_by="chunker.py::fallback_split",
                    )
                )
                index += 1
            start += chunk_size - overlap

    return chunks


# ─── My strategy: one chunk per labeled section ──────────────────────────────
#
# city_guides is fourteen documents of ~2,000 characters each, every one laid
# out as "# Town" → a short intro → "## Getting there", "## Eat and drink",
# "## When to go" and so on. Each section answers one kind of question and
# runs 175–710 characters. The heading IS the topic boundary, so that is where
# the cut goes, not at character 800.
#
# Two things a bare section would lose, and how I keep them:
#   1. Which town it is about. "Buses run from Brightwater roughly hourly" sits
#      under "## Getting there" in guide_kestrelford.md and never says
#      "Kestrelford". So every chunk is prefixed with "<guide title> — <section>".
#   2. Nothing else. Overlap is 0: the neighboring section is a different
#      topic ("Eat and drink" after "Getting around"), and dragging it in would
#      make every chunk match two kinds of question a little and neither well.
#      The heading prefix does the job overlap normally does — carrying context.
#
# The cross-town guides (accessibility, walking) put several towns in one
# section, one bold-led paragraph per town ("**Marchwood** has a modern tram
# network..."). Those split one paragraph per chunk, still prefixed, so a
# question about Marchwood doesn't drag Thornby Wells and Brightwater along.
#
# SECTION_MAX_CHARS is a safety net, not the strategy: nothing in this corpus
# reaches it, but a section that did would split at paragraph boundaries.
#
# Unit 2 improvement — resolve "there" in headings. "Getting there" is a
# dangling reference: the body describes the route FROM other towns ("four
# buses a day from Brightwater") and never names the town it's about, so the
# heading was the only link to it and the heading said "there". In the unit 2
# diagnosis that section missed the top 5 for "How do I get to X?" in 6 of 9
# towns. _resolve_heading turns "Getting there" into "Getting to Kestrelford",
# the same rule as the title prefix: a chunk has to make sense on its own.

SECTION_MAX_CHARS = 900
MIN_PARAGRAPH_CHARS = 60   # don't split off a lone one-line paragraph


def _resolve_heading(heading: str, title: str) -> str:
    """'Getting there' -> 'Getting to <title>'. Other headings unchanged."""
    import re

    return re.sub(r"\bthere\b", f"to {title}", heading)


def _title_of(text: str, fallback: str) -> str:
    for line in text.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return fallback


def _split_sections(text: str) -> list[tuple[str, str]]:
    """[(heading, body)] in document order. The intro gets heading 'Overview'."""
    import re

    out: list[tuple[str, str]] = []
    heading = "Overview"
    body: list[str] = []
    for block in text.split("\n\n"):
        block = block.strip()
        if not block:
            continue
        if block.startswith("# "):            # document title — not content
            rest = block.split("\n", 1)
            if len(rest) > 1:
                body.append(rest[1].strip())
            continue
        m = re.match(r"^##+\s+(.*?)(?:\n+(.*))?$", block, re.S)
        if m:
            if body:
                out.append((heading, "\n\n".join(body)))
            heading, body = m.group(1).strip(), []
            if m.group(2):
                body.append(m.group(2).strip())
        else:
            body.append(block)
    if body:
        out.append((heading, "\n\n".join(body)))
    return out


def _pieces(body: str) -> list[str]:
    """One section body → one or more chunk bodies."""
    paras = [p.strip() for p in body.split("\n\n") if p.strip()]

    # Cross-town sections: one paragraph per town.
    if sum(p.startswith("**") for p in paras) >= 2:
        merged: list[str] = []
        for p in paras:
            if merged and (not p.startswith("**") or len(p) < MIN_PARAGRAPH_CHARS):
                merged[-1] += "\n\n" + p
            else:
                merged.append(p)
        return merged

    if len(body) <= SECTION_MAX_CHARS:
        return [body]

    # Safety net: pack whole paragraphs up to the cap. Never cuts a sentence.
    out, cur = [], ""
    for p in paras:
        if cur and len(cur) + 2 + len(p) > SECTION_MAX_CHARS:
            out.append(cur)
            cur = p
        else:
            cur = f"{cur}\n\n{p}" if cur else p
    if cur:
        out.append(cur)
    return out


def split_documents(documents: list[Document]) -> list[Chunk]:
    """
    Section-aware chunking for structured guides. One chunk per `##` section
    (plus one for the intro), each prefixed with "<guide title> — <section>"
    so it still makes sense pulled out on its own. Overlap 0. See the notes
    above for why.
    """
    chunks: list[Chunk] = []
    for doc in documents:
        title = _title_of(doc.text, doc.source)
        index = 0
        for heading, body in _split_sections(doc.text):
            for piece in _pieces(body):
                chunks.append(
                    Chunk(
                        text=f"{title} — {_resolve_heading(heading, title)}\n\n{piece}",
                        source=doc.source,
                        index=index,
                        produced_by="chunker.py::split_documents",
                    )
                )
                index += 1
    return chunks


def describe(chunks: list[Chunk]) -> str:
    """A one-line summary, printed after indexing."""
    if not chunks:
        return "0 chunks"
    lengths = [len(c.text) for c in chunks]
    return (
        f"{len(chunks)} chunks, "
        f"{sum(lengths) // len(lengths)} characters on average "
        f"(shortest {min(lengths)}, longest {max(lengths)}), "
        f"produced by {chunks[0].produced_by}"
    )


if __name__ == "__main__":
    from ingest import load_documents

    chunks = split_documents(load_documents())
    print(describe(chunks))
