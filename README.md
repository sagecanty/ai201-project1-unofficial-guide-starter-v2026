# The Unofficial Guide

Sezgi — corpus: `city_guides`

> **This file is your submission.** Fill it in as you go — most sections get
> written during the milestone that produces them, not at the end.
>
> How the starter works, and every command you'll need, is in `RUNNING.md`.
> Leave that file alone.
>
> **Paste everything as text.** No screenshots, no video. A typed table gets
> full credit; a picture of the same table gets none.
>
> Delete these instruction blocks as you replace them. The `<!-- -->` comments
> are notes to you and don't show up when the page renders — you can leave them
> or remove them.

---

# Unit 1

## What This Does

<!-- Three or four sentences. Which corpus you picked, and the kinds of
     questions your system answers. Write it for someone who has never seen
     this repo.

     Milestone 5. -->

## Chunking Strategy

**Chunk size:** one chunk per `##` section of a guide — 183 to 661 characters,
306 on average, 90 chunks from 14 documents. A 900-character cap exists as a
safety net (`SECTION_MAX_CHARS` in `chunker.py`) but nothing in this corpus
reaches it. In the two cross-town guides (accessibility, walking), sections
that list several towns as bold-led paragraphs split one town per chunk.

**Overlap:** 0. Instead, every chunk starts with `<guide title> — <section heading>`.

**What about the documents made me pick this.** Reading the guides in
Milestone 1, every one is laid out the same way: `# Town`, a two-sentence
intro, then `## Getting there`, `## Getting around`, `## Eat and drink`,
`## What to see`, `## Where to stay`, `## When to go`. Each section answers
exactly one kind of question, and each is short (175–710 characters). The
heading is already the topic boundary, so that's where I cut.

The starter's 800-character windows ignored that. On this corpus they made
51 chunks averaging 650 characters, 9 of which contain both "Getting there"
and "Getting around", and the shortest was 24 characters of the tail of a
sentence: `'d Sundays and after 5pm.'` (guide_eating.md#3). A chunk spanning two or
three sections matches every question about that town a little and none of
them well.

Why the title prefix instead of overlap: a section on its own often never
names its town. `Buses run from Brightwater roughly hourly on weekdays` is in
guide_kestrelford.md under "Getting there" and the word "Kestrelford" isn't in
it. Overlap with the neighboring section wouldn't fix that — the neighbor is
"Getting around", a different topic, and dragging it in would dilute the chunk.
Prefixing `Kestrelford — Getting there` carries the context overlap is
normally there for, without the noise.

Why split the cross-town sections further: guide_accessibility.md's
"Straightforward" section covers Thornby Wells, Marchwood and Brightwater in
three paragraphs. As one chunk, a question about Marchwood's trams would
retrieve a chunk two-thirds about other towns. Each paragraph opens with the
town in bold, so that's a clean boundary.

**Cleaning, which mattered as much as chunking.** All nine town guides end
with an identical "Practical notes" paragraph — word for word the same — that
says the nearest full hospital is in Brightwater. guide_accessibility.md says
it's Marchwood. That paragraph is template boilerplate, and left in it would be
nine chunks outvoting the one document that's right. `ingest.py` now drops any
`##` section whose text appears identically in 3 or more documents (9 removed
here; the eating guide's own different "Practical" section survives). It also
un-wraps the hard line breaks some guides have at ~80 columns.

**What I'd watch:** the intro chunk of guide_accessibility.md (Chunk 1 below)
is the weakest chunk in the set. It's a sentence about the guide, not about the
region, and can't answer any question on its own. It's harmless — nothing
should rank it first — but it's the first thing I'd check if retrieval looks
odd in unit 2.

## Sample Chunks

All five printed by `python app.py chunks -n 5`.

**Chunk 1** — source: `guide_accessibility.md#0` — produced by: `chunker.py::split_documents`

```
Getting around the region with limited mobility — Overview

An honest assessment rather than a promotional one. Some of these places are difficult and it is better to know in advance.
```

**Chunk 2** — source: `guide_corry_vale.md#1` — produced by: `chunker.py::split_documents`

```
Corry Vale — Getting there

There is no public transport into the valley beyond a school bus that will carry passengers if there is room. Driving from Brightwater takes 35 minutes on a good road as far as the valley mouth and then 20 more on a poor one. Cycling in is a serious undertaking; the road climbs 400 metres in the first four miles.
```

**Chunk 3** — source: `guide_givens_mill.md#0` — produced by: `chunker.py::split_documents`

```
Givens Mill — Overview

Givens Mill is a village of 700 built around a working watermill that still grinds flour commercially. It is the sort of place people visit for an afternoon and then talk about for longer than the visit lasted.
```

**Chunk 4** — source: `guide_kestrelford.md#4` — produced by: `chunker.py::split_documents`

```
Kestrelford — What to see

The market square on a Saturday morning is the main event and has run continuously since the 1400s. The parish church has a 13th-century tower you can climb for £2. The old trackbed walk runs six miles to the next village along an easy gradient and is the best half-day here.
```

**Chunk 5** — source: `guide_regional_transport.md#1` — produced by: `chunker.py::split_documents`

```
Getting around the region — Buses

Three operators run in the region and they do not accept each other's tickets, which is the single most common source of confusion for visitors. Services concentrate on weekday daytimes. Sunday service is minimal to non-existent outside the Brightwater town routes.

The Kestrelford service is hourly on weekdays, two-hourly on Saturdays, and does not run on Sundays. The Halden Bay coast service runs four times daily year-round.
```

## Sample Answer

<!-- One complete question and answer, pasted as text, with the source line
     visible. Milestone 4. -->

**Question:**

**Answer:**

```
```

**My relevance cutoff:**

<!-- The number you set in config.py, and how you got there.

     You ran five questions your corpus covers and the five in OUT_OF_SCOPE
     that it clearly doesn't, and wrote down the best distance for each. What
     did those two groups look like? Where was the gap? Put the actual numbers
     here — the table below wants all ten rows.

     Milestone 4. -->

| Question | In corpus? | Best distance |
|---|---|---|
|  |  |  |

## How I Used AI

<!-- Two specific moments. For each: what you asked for, what came back, and
     what you changed about it.

     "I asked Claude to write the chunking function from my notes. It ignored
     the overlap, so I added that myself" is the level of detail we're after.
     "I used AI to help me code" is not.

     Milestone 5. -->

**1.**

**2.**

<!-- ── Stretch features ─────────────────────────────────────────────────────
     Doing one? Say so here BEFORE you start. A feature this README never
     claims earns nothing.
     ───────────────────────────────────────────────────────────────────────── -->

---

# Unit 2

<!-- These sections get ADDED to what's already above. Don't delete or rewrite
     unit 1 — the point is that someone can see what you said before you knew
     how it went. -->

## Run Log — Before

<!-- Your five criteria, three runs each. `python run_eval.py --label before`
     runs the questions, puts the OUT_OF_SCOPE ones through the gate, and
     writes it all into results/ for you. Targets come from criteria.md; the
     verdict column is your call.

     Criterion 3 is measured in one deterministic pass rather than three, so
     the same number goes in all three run columns. That's correct, not lazy.

     Milestone 1. -->

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. Retrieved chunk contains the answer | 4 of 5 |  |  |  |  |
| 2. Every answer names a source | 5 of 5 |  |  |  |  |
| 3. Gate stops out-of-corpus questions | 4 of 5 |  |  |  |  |
| 4. | | | | | |
| 5. | | | | | |

<!-- Underneath, paste the REAL output for each criterion from one of your
     runs — the actual text your system produced, not a description of it.
     Name the file and function that produced it. -->

## Verdicts

<!-- MET or MISSED for each of the five, against the target you wrote last
     unit — not a new one. Plus a sentence on how you decided. That sentence
     matters most where it was close.

     If your target said 4 of 5 and your runs came out 4, 3, 4, that's a MISS.
     The target has to hold, not show up occasionally.

     Milestone 2. -->

| # | Criterion | Verdict | How I decided |
|---|---|---|---|
| 1 |  |  |  |
| 2 |  |  |  |
| 3 |  |  |  |
| 4 |  |  |  |
| 5 |  |  |  |

## Diagnoses

<!-- For each miss: which stage caused it, and how. The stage alone isn't
     enough — you need the mechanism.

     Not a diagnosis: "Question 3 didn't work."
     A diagnosis:     "Question 3 asks about laundry costs. The answer is in
                       one sentence that got split across two chunks, so
                       neither chunk on its own contains it."

     The five stages: loading → chunking → embedding → retrieval → generation.

     Look for a pattern. If three misses all ask about numbers, that's one
     problem, not three.

     Missed nothing? Say so, then say honestly whether your targets were set
     low, and which one you'd tighten and to what.

     Milestone 3. -->

## The Improvement

**What I changed:**

**Why I picked it:**

<!-- Connect it to a specific diagnosis above in one sentence. If you can't,
     you picked a fix because it sounded impressive. -->

### Run Log — After

<!-- Same format, same five criteria, three runs each.
     `python run_eval.py --label after` -->

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. Retrieved chunk contains the answer | 4 of 5 |  |  |  |  |
| 2. Every answer names a source | 5 of 5 |  |  |  |  |
| 3. Gate stops out-of-corpus questions | 4 of 5 |  |  |  |  |
| 4. | | | | | |
| 5. | | | | | |

**Did it help?**

<!-- Say plainly whether it did, and how you know. If it made things worse,
     say that — a change that backfired, honestly reported, earns full credit
     and is more interesting than one that worked. What matters is that you can
     tell.

     Milestone 4. -->

## What's Still Broken

<!-- For each criterion still missed after your fix: what you'd do about it,
     and why you stopped where you did.

     "I ran out of time" is fine if it's true. Pretending nothing is left is
     not.

     Milestone 5. -->

## What I'd Do Differently

<!-- Knowing what you know now — which of your five criteria would you write
     differently, and why?

     Milestone 5. -->
