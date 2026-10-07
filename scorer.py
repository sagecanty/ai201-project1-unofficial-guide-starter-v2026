"""
Decides whether one answer was right. `run_eval.py` finds `judge` and uses it.

Written before the first unit 2 run, so the rule was fixed before any answer
existed to tune it against.

The rule: the answer passes if it contains the question's `expects` phrase
from questions.py, after normalizing both sides. A gate refusal always fails,
because every one of my five test questions is answerable from the corpus.

Normalizing means: lowercase, drop everything that isn't a letter or digit
(so "10am", "10 am" and "10 a.m." all match), and treat number words one to
twelve as their digits (so "six times" and "6 times" both match). That's as
generous as it gets. It does NOT accept "10:00" for "10am" or "every hour" for
"hourly" — I'd rather see those fail and read them than quietly pass them.
"""

import re

import gate

_NUMBERS = {
    "one": "1", "two": "2", "three": "3", "four": "4", "five": "5", "six": "6",
    "seven": "7", "eight": "8", "nine": "9", "ten": "10", "eleven": "11",
    "twelve": "12",
}


def normalize(text: str) -> str:
    words = re.findall(r"[a-z0-9]+", text.lower())
    return "".join(_NUMBERS.get(w, w) for w in words)


def judge(question, expects, answer, results) -> bool:
    if not expects or answer.strip() == gate.REFUSAL:
        return False
    return normalize(expects) in normalize(answer)
