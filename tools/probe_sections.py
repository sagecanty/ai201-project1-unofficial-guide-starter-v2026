#!/usr/bin/env python3
"""
Diagnostic probe for the unit 2 diagnosis. Retrieval only, no model calls.

My five test questions all contain a distinctive word ("flood", "parking",
"hospital"). The one failure I've seen, "how do I get to Kestrelford?", is a
short question whose only distinctive word is the town. This asks the same
kind of question for every town guide and every standard section, and records
where the one chunk that answers it lands:

    python tools/probe_sections.py            # current pipeline
    python tools/probe_sections.py --top-k 8  # same, deeper cut

It is NOT a replacement for the five-question test in questions.py; that test
and its criteria stay exactly as written in unit 1. This is evidence for a
diagnosis, written after the before-run, and labeled as such in the README.
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import config  # noqa: E402
from store import search  # noqa: E402

TOWNS = [
    "Brightwater", "Corry Vale", "Elder Ness", "Givens Mill", "Halden Bay",
    "Kestrelford", "Marchwood", "Pellew Sands", "Thornby Wells",
]
TEMPLATES = {
    "Getting there": "How do I get to {t}?",
    "Getting around": "How do I get around {t}?",
    "Eat and drink": "Where can I eat in {t}?",
    "What to see": "What is there to see in {t}?",
    "Where to stay": "Where should I stay in {t}?",
    "When to go": "When is the best time to visit {t}?",
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--top-k", type=int, default=config.TOP_K)
    ap.add_argument("--variant", default="default")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    deep = 20
    ranks = []
    by_section = {s: [] for s in TEMPLATES}
    for section, tmpl in TEMPLATES.items():
        for town in TOWNS:
            q = tmpl.format(t=town)
            res = search(q, top_k=deep, corpus=config.CORPUS, variant=args.variant)
            want = f"{town} — {section}"
            rank = next(
                (i + 1 for i, r in enumerate(res) if r.text.startswith(want)), None
            )
            ranks.append(rank)
            by_section[section].append(rank)
            if not args.quiet:
                same_town = sum(r.text.startswith(f"{town} —") for r in res[: args.top_k])
                print(f"  rank {str(rank or '>20'):>3}  same-town chunks in top {args.top_k}: "
                      f"{same_town}  | {q}")

    def hit(rs, k):
        return sum(1 for r in rs if r and r <= k)

    n = len(ranks)
    print(f"\n{n} probes, variant '{args.variant}'")
    print(f"  right chunk at rank 1:      {hit(ranks, 1)}/{n}")
    print(f"  right chunk in top {args.top_k}:       {hit(ranks, args.top_k)}/{n}")
    print(f"  right chunk in top 8:       {hit(ranks, 8)}/{n}")
    print("\n  by section (rank 1 / top %d):" % args.top_k)
    for s, rs in by_section.items():
        print(f"    {s:15s} {hit(rs, 1)}/9  {hit(rs, args.top_k)}/9")


if __name__ == "__main__":
    main()
