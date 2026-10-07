#!/usr/bin/env python3
"""
Turn a run_eval.py log (one row per QUESTION) into my run log (one row per
CRITERION), using the exact checks below. Measurement only — nothing in the
pipeline imports this file.

    python criteria_check.py results/run_..._before.md

Written before the first unit 2 run. How each criterion in criteria.md is
counted:

  1. Retrieved chunk contains the answer — for each question, do any of the
     top-k chunks from store.search contain its `expects` phrase (normalized
     the same way scorer.py does)? Retrieval is deterministic, so this is
     measured once and the same count goes in all three run columns. Run this
     against the same code that produced the log, or the count is meaningless.
  2. Every answer names a source — does the answer text contain a filename
     ending in .md? Out of the answers the model actually wrote; a gate refusal
     isn't an answer (criteria.md says so), and is reported separately.
  3. Gate stops out-of-corpus questions — read straight off the log's
     "Refused X of Y" line.
  4. Best chunk wins outright — does the rank-1 chunk contain `expects`?
     Deterministic, like criterion 1.
  5. Cited file is the right file — take the answer's last "Source:" line,
     pull out every *.md filename on it, and pass only if there is at least
     one and every one is in the question's `answer_in` list. No Source: line
     at all is a fail: there is nothing to check, and the prompt asks for one.
"""

import re
import sys
from pathlib import Path

import config
import questions as qs
from scorer import normalize

TARGETS = {1: (4, 5), 2: (5, 5), 3: (4, 5), 4: (3, 5), 5: (4, 5)}
NAMES = {
    1: "Retrieved chunk contains the answer",
    2: "Every answer names a source",
    3: "Gate stops out-of-corpus questions",
    4: "Rank-1 chunk contains the answer",
    5: "Cited file is in the answer key",
}
REFUSAL_PREFIX = "I don't have enough information about that"
FILENAME = re.compile(r"[\w-]+\.md")
SOURCE_LINE = re.compile(r"(?im)^\W*sources?\W*:\s*(.+)$")


def parse_log(path: Path):
    text = path.read_text(encoding="utf-8")
    blocks = re.findall(
        r"^### (.+?) — run (\d+)\n.*?```\n(.*?)\n```", text, re.S | re.M
    )
    answers = {}
    for question, run, answer in blocks:
        answers.setdefault(int(run), {})[question.strip()] = answer.strip()
    m = re.search(r"Refused (\d+) of (\d+)", text)
    gate = (int(m.group(1)), int(m.group(2))) if m else None
    return answers, gate


def cited_files(answer: str) -> list[str]:
    lines = SOURCE_LINE.findall(answer)
    return FILENAME.findall(lines[-1]) if lines else []


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    path = Path(sys.argv[1])
    answers, gate = parse_log(path)
    runs = sorted(answers)
    items = qs.answered()

    from store import search

    c1 = c4 = 0
    detail = []
    for item in items:
        res = search(item["question"], top_k=config.TOP_K, corpus=config.CORPUS)
        want = normalize(item["expects"])
        ranks = [i + 1 for i, r in enumerate(res) if want in normalize(r.text)]
        c1 += bool(ranks)
        c4 += ranks[:1] == [1]
        detail.append((item["question"], ranks, res[0].label if res else "-"))

    cols = {k: [] for k in NAMES}
    per_q = []
    for run in runs:
        written = named = right = 0
        for item in items:
            ans = answers[run].get(item["question"], "")
            refused = ans.startswith(REFUSAL_PREFIX) or not ans
            cites = cited_files(ans)
            ok5 = bool(cites) and all(c in item["answer_in"] for c in cites)
            if not refused:
                written += 1
                named += bool(FILENAME.search(ans))
            right += ok5
            per_q.append((run, item["question"], refused, cites, ok5))
        n = len(items)
        cols[1].append(f"{c1}/{n}")
        cols[2].append(f"{named}/{written}")
        cols[3].append(f"{gate[0]}/{gate[1]}" if gate else "?")
        cols[4].append(f"{c4}/{n}")
        cols[5].append(f"{right}/{n}")

    def holds(k):
        need, of = TARGETS[k]
        for cell in cols[k]:
            got, den = map(int, cell.split("/"))
            if k == 2:
                if got != den or den == 0:
                    return False
            elif got < need:
                return False
        return True

    print(f"Run log from {path.name}\n")
    print("| Criterion | Target | " + " | ".join(f"Run {r}" for r in runs) + " | Verdict |")
    print("|---|---|" + "---|" * len(runs) + "---|")
    for k in NAMES:
        need, of = TARGETS[k]
        verdict = "MET" if holds(k) else "MISSED"
        print(f"| {k}. {NAMES[k]} | {need} of {of} | " + " | ".join(cols[k]) + f" | {verdict} |")

    print("\nRetrieval detail (criteria 1 and 4):")
    for q, ranks, top in detail:
        print(f"  expects at ranks {ranks or 'none'}; rank 1 = {top}  | {q}")
    print("\nCitation detail (criteria 2 and 5):")
    for run, q, refused, cites, ok5 in per_q:
        tag = "REFUSED " if refused else ""
        print(f"  run {run}: {tag}cites {cites or 'NO Source: line'} -> {'ok' if ok5 else 'FAIL'}  | {q}")


if __name__ == "__main__":
    main()
