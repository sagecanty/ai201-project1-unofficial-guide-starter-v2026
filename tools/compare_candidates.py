#!/usr/bin/env python3
"""
Unit 2 diagnosis: cost out three candidate fixes on retrieval alone, before
picking ONE to ship. No model calls. The shipped system is not touched; the
heading candidate is indexed as a separate variant ("probe_heading").

    python tools/compare_candidates.py

Candidates:
  (a) hybrid: BM25 over chunk text fused with the dense ranking (RRF, k=60)
  (b) top-k 8 instead of 5, dense ranking unchanged
  (c) heading: "<Town> — Getting there" → "<Town> — Getting to <Town>"

Probe sets:
  sections   — the 54 questions from tools/probe_sections.py
  held-out   — 18 "getting there" questions in wording I did not use while
               diagnosing, to check (c) isn't just matching my own phrasing
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import config  # noqa: E402
from chunker import split_documents  # noqa: E402
from ingest import load_documents  # noqa: E402
from store import build_index, search  # noqa: E402
from probe_sections import TEMPLATES, TOWNS  # noqa: E402

HELD_OUT = [
    "What's the best way to reach {t}?",
    "Is there a train or bus to {t}?",
]
DEEP = 20


def heading_variant(chunks):
    for c in chunks:
        title = c.text.split(" — ", 1)[0]
        c.text = c.text.replace(f"{title} — Getting there", f"{title} — Getting to {title}", 1)
    return chunks


def tok(text):
    return re.findall(r"[a-z0-9]+", text.lower())


def main():
    base = split_documents(load_documents())
    texts = [c.text for c in base]

    from rank_bm25 import BM25Okapi
    bm25 = BM25Okapi([tok(t) for t in texts])

    build_index(heading_variant(split_documents(load_documents())),
                corpus=config.CORPUS, variant="probe_heading")

    def dense(q, variant="default"):
        return [r.text for r in search(q, top_k=DEEP, corpus=config.CORPUS, variant=variant)]

    def hybrid(q):
        d = dense(q)
        scores = bm25.get_scores(tok(q))
        b = [texts[i] for i in sorted(range(len(texts)), key=lambda i: -scores[i])[:DEEP]]
        fused = {}
        for ranking in (d, b):
            for r, t in enumerate(ranking):
                key = t.replace("Getting to", "Getting there")
                fused[key] = fused.get(key, 0) + 1 / (60 + r + 1)
        return sorted(fused, key=lambda t: -fused[t])

    systems = {
        "baseline (top-5)": (lambda q: dense(q), 5),
        "(a) hybrid, top-5": (hybrid, 5),
        "(b) dense, top-8": (lambda q: dense(q), 8),
        "(c) heading, top-5": (lambda q: dense(q, "probe_heading"), 5),
    }

    def rank_of(ranking, town, section):
        for i, t in enumerate(ranking):
            head = t.split("\n", 1)[0]
            if head == f"{town} — {section}" or (
                section == "Getting there" and head == f"{town} — Getting to {town}"
            ):
                return i + 1
        return None

    sets = {
        "sections (54)": [(tmpl.format(t=t), t, s) for s, tmpl in TEMPLATES.items() for t in TOWNS],
        "getting-there only (9)": [(TEMPLATES["Getting there"].format(t=t), t, "Getting there") for t in TOWNS],
        "held-out getting-there (18)": [(h.format(t=t), t, "Getting there") for h in HELD_OUT for t in TOWNS],
    }

    print(f"{'system':22s} | " + " | ".join(f"{name}: @1 / in-k" for name in sets))
    for name, (fn, k) in systems.items():
        cells = []
        for probes in sets.values():
            ranks = [rank_of(fn(q), t, s) for q, t, s in probes]
            n = len(ranks)
            at1 = sum(r == 1 for r in ranks)
            ink = sum(1 for r in ranks if r and r <= k)
            cells.append(f"{at1}/{n} / {ink}/{n}")
        print(f"{name:22s} | " + " | ".join(cells))


if __name__ == "__main__":
    main()
