# Acceptance criteria — The Unofficial Guide

Five criteria that say what "working" means for this system, written in unit 1
**before** any results existed.

An acceptance criterion names a target: a number, a count, a rate, or something
a person could plainly observe. *"Retrieval works"* is an opinion. *"For at
least 4 of my 5 test questions, the top results include a chunk containing the
answer"* is a criterion.

Under each one, write a sentence or two on **why that target** and not a
stricter or looser one. A reason that says something about your corpus or your
pipeline earns credit; *"80% seemed reasonable"* does not.

> Missing your own targets next unit costs you nothing. Setting a target so
> easy you can't miss it does.

---

## 1. Retrieved chunks contain the answer

For at least 4 of my 5 test questions, the retrieved chunks include one that
contains the answer.

**Why this target:**
Three of my questions have their answer stated in two or three guides, so
retrieval gets several chances at them. Question 4 ("easiest to visit with
limited mobility") is answered by exactly one chunk in guide_accessibility.md,
while nine town guides each have a "Getting around" section using most of the
same words. That one could plausibly lose to lookalikes, so 5 of 5 would be
assuming the problem away; 3 of 5 would excuse a miss on a question with two
separate source documents.

---

## 2. Every answer names a source

Every answer the system produces names at least one source document.

**Why this target:**
All of them, because I'm tightening the grounding instruction in generate.py
to require a final line in the form `Source: <filename>`, and every excerpt
the model sees is already labeled with its filename. The only way this fails
is the model ignoring an explicit formatting rule — and that is exactly the
failure I want to know about, so I'm not allowing for it. "Answer" means text
the model wrote; a gate refusal never reaches the model and isn't counted.

---

## 3. The relevance gate stops out-of-corpus questions

When I ask a question my documents clearly don't cover, the relevance gate
stops it and the system returns "I don't have enough information about that" —
in at least 4 of 5 tries.

<!-- The five questions are the ones in `OUT_OF_SCOPE` at the bottom of
     `questions.py`, and `run_eval.py` puts them through the gate and writes
     what happened into your run log. Swap them for your own if you'd rather —
     just keep five of them, or the "4 of 5" above has nothing to be 4 of. -->

**Why this target:**
The five OUT_OF_SCOPE questions are from a different world, but two have a
hook into this corpus: the ibuprofen question shares medical vocabulary with
the hospital chunk, and "change the oil in a diesel engine" shares driving
vocabulary with the regional transport guide's "Driving" section. I'm setting
the cutoff from measured distances in Milestone 4, but before measuring I
can't claim neither will slip under it, so 4 of 5. Missing two would mean
the gap I set the cutoff in isn't real.

---

## 4. The best chunk wins outright

For at least 3 of my 5 test questions, the single closest chunk (rank 1 in
`python app.py retrieve "<question>"`) contains that question's `expects`
phrase from questions.py.

**Why this target:**
Criterion 1 is satisfied by the right chunk sitting at rank 5 under four wrong
ones; this one asks whether my chunks are the right size to win. Too big (the
starter's 800-character windows straddle two or three sections) and the answer
is diluted by neighboring topics, so a focused wrong chunk outranks it. Too
small and the chunk loses which town it's about. 3 and not 4 because question
2 has to bridge "August" to "summer weekends" and question 4 competes with
nine lookalike "Getting around" sections — I expect at least one of those to
land at rank 2 or 3 rather than 1.

---

## 5. The cited file is the right file

In at least 4 of my 5 test answers, every filename on the answer's `Source:`
line is one of the files listed in that question's `answer_in` field in
questions.py.

**Why this target:**
Criterion 2 only checks that a source is named, not that it's the right one,
and in this corpus that difference is real: the same fact often appears in a
town guide and a cross-cutting guide, and nine town guides carry an identical
pasted "Practical notes" paragraph saying the nearest full hospital is in
Brightwater, when guide_accessibility.md says Marchwood. I plan to strip it at
ingestion; this criterion is how I'd know if it leaked back in. A confident
answer citing guide_brightwater.md would pass criterion 2 and be wrong. 4 and
not 5 because the model sees five excerpts from up to five files and may list
an extra one it glanced at; that's one sloppy citation, not a broken system. 3
would let a systematic citation problem hide.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     UNIT 2 — read this before you change anything above.

     If a criterion turns out to be BROKEN rather than merely unmet, you can
     revise it, and that earns credit. But never delete or edit the original
     line. Add the revision underneath it, like this:

         ## 1. Retrieved chunks contain the answer

         For at least 4 of my 5 test questions, the retrieved chunks include
         one that contains the answer.

         **Why this target:** ...

         > **Revised in unit 2:** For at least 4 of 5 questions, the top three
         > results contain the answer.
         >
         > **Why revised:** I couldn't judge "the chunks include one that
         > contains the answer" the same way twice — I scored two questions
         > differently on Monday than on Wednesday. The new version is
         > something I can actually check.

     That's a revision because the criterion couldn't be MEASURED.

     Lowering a target because you missed it is not a revision, and it costs
     you the point:

         ✗ "I said 4 of 5 but got 2 of 5, so 2 of 5 is more realistic."

     A number you missed stays where it is, gets diagnosed, and gets a fix
     attempted. That's where the points are.

     The whole reason the originals stay visible is so someone can see what you
     said before you knew the answer.
     ───────────────────────────────────────────────────────────────────────── -->
