# The Unofficial Guide

Sezgi — corpus: `city_guides`

---

# Unit 1

## What This Does

A question-answering system over `city_guides`: fourteen travel guides to a
fictional region — nine town guides (Kestrelford, Halden Bay, Elder Ness,
Marchwood and others) and five that cut across all of them (transport,
walking, eating, seasons, accessibility). Ask it something like "How often do
buses run from Brightwater to Kestrelford on weekdays?" or "Which town is
easiest to visit with limited mobility?" and it answers from the guides only,
ending with a `Source:` line naming the file. Questions from outside the region
entirely ("Who won the 1994 World Cup?") are refused by a relevance gate
before the model ever runs; questions about the region that the guides don't
cover ("Is there a cinema in Kestrelford?") get an honest "the documents don't
say". Run it with `python app.py ask "your question"`.

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

**Question:** Where is the nearest full hospital in the region?

**Answer:**

```
$ python app.py ask "Where is the nearest full hospital in the region?"
  (best distance 0.407, cutoff 0.61)

The nearest full hospital is located in Marchwood.

Source: guide_accessibility.md

Sources retrieved: guide_accessibility.md, guide_givens_mill.md
```

I picked this one because it's the question the boilerplate cleaning exists
for. Before `ingest.py` stripped the nine identical "Practical notes"
paragraphs, nine chunks said "the nearest full hospital is in Brightwater"
and one said Marchwood.

**My relevance cutoff:** 0.61 (`THRESHOLD` in `config.py`), top-k 5.

Best distance for each question, from `app.py retrieve` with my chunker:

| Question | In corpus? | Best distance |
|---|---|---|
| How often do buses run from Brightwater to Kestrelford on weekdays? | Yes | 0.208 |
| What time should I get to Halden Bay in August if I want a parking space? | Yes | 0.258 |
| How many times a year does the road to Elder Ness flood? | Yes | 0.282 |
| Which town in the region is easiest to visit with limited mobility? | Yes | 0.333 |
| Where is the nearest full hospital in the region? | Yes | 0.407 |
| What is the capital of Mongolia? | No | 0.810 |
| What is the recommended dosage of ibuprofen for a headache? | No | 0.835 |
| How do I write a for loop in Rust? | No | 0.861 |
| How do I change the oil in a diesel engine? | No | 0.881 |
| Who won the 1994 World Cup? | No | 0.969 |

The two groups don't come close: in-corpus tops out at 0.407, out-of-corpus
starts at 0.810. I put the cutoff at 0.61, the midpoint, which leaves about 0.2
of headroom on each side — room for an in-corpus question phrased worse than
mine, and for an off-topic one that happens to share a word with the guides.
The two I worried about in criterion 3 (ibuprofen and the diesel engine) came
in at 0.835 and 0.881, nowhere near.

The gap is that wide because these out-of-scope questions are *very* out of
scope. So I also tried five "near misses" — questions about these towns that
the guides just don't answer:

| Near-miss question | Best distance |
|---|---|
| How much does a taxi from Marchwood to Brightwater cost? | 0.353 |
| Is there a cinema in Kestrelford? | 0.366 |
| What is the population of Halden Bay? | 0.385 |
| Are there any vegan restaurants in Thornby Wells? | 0.407 |
| Can I bring my dog on the Pellew Sands land train? | 0.523 |

Those sit *inside* the in-corpus range. No cutoff can stop them without also
refusing the hospital question, so the gate isn't the right layer for them —
the grounding prompt is. With the tightened prompt, "Is there a cinema in
Kestrelford?" got: *"I do not have enough information to answer whether there
is a cinema in Kestrelford, as the provided documents do not mention one."*

**What I changed in the grounding prompt** (`GROUNDING_INSTRUCTION` in
`generate.py`): three rules added on top of the starter's. Use only excerpts
about the town the question asks about and never carry a fact across towns
(nine guides have identically named sections, so this is the likeliest kind of
drift). If excerpts disagree, say so and name both files. And end with a
`Source: <filename>` line, which is what criteria 2 and 5 check.

**One thing that went wrong, kept for unit 2.** "how do I get to Kestrelford?"
answered fine with the starter's chunker (though it said the last stretch of
road is "eight miles" — the guides say eight *minutes*). With my chunker it
answered *"the documents do not provide specific instructions on how to travel
there."* `app.py retrieve` shows why: the top five were Kestrelford's "Where to
stay" (0.321), "Getting around", "Overview", an accessibility chunk, and "Eat
and drink" — "Getting there" didn't make the top 5. The `Kestrelford — ...`
prefix I added makes every Kestrelford chunk similar to any question with
"Kestrelford" in it, and in a short question the town name outweighs the topic.
The prompt did its job (it declined instead of inventing), but retrieval
failed. My five test questions all contain distinctive words ("flood",
"parking", "hospital") that dodge this, which is worth knowing before I trust
my criterion 1 results.

## How I Used AI

I used Claude (Opus 5.5, in the Claude app, connected to my Mac) for most of
this unit: it read the brief and the corpus, wrote the code changes, ran the
pipeline on my machine, and drafted the README and criteria 4 and 5. The brief
says not to have AI write criteria, so to be clear: criteria 4 and 5 and all
five "why this target" paragraphs were drafted by Claude, not me. Two moments
worth recording:

**1. The criteria described work that didn't exist yet.** Claude's first draft
of criteria.md said the grounding prompt "now requires" a `Source:` line, and
that the hospital boilerplate had been cleaned "before" — but at the Milestone
2 commit, neither change had been made. Committed as written, the history
would have claimed results before they existed, which is the one thing that
history is there to prove. It caught this before committing and rewrote both
as plans ("I'm tightening the grounding instruction", "I plan to strip it at
ingestion"), then committed criteria and questions on their own, ahead of the
chunker. The same fix went into a comment in questions.py.

**2. The chunk prefix helped my test questions and broke a plain one.** Claude
designed the chunker to prefix every chunk with `<town> — <section>`, because
sections like "Getting there" often never say which town they're about. My five
test questions all retrieved the right chunk. But when it re-ran the
Milestone 1 question "how do I get to Kestrelford?", the answer said the
documents don't explain how to get there. `app.py retrieve` showed "Kestrelford
— Getting there" wasn't in the top 5: with "Kestrelford" in every chunk's
prefix, the town name outweighed the topic. Rather than patch it to make the
unit 1 numbers look better, we kept the chunker as it was and wrote the miss up
under Sample Answer as the first thing to diagnose in unit 2.

(Smaller one: the embedder crashed on my Intel Mac with an onnxruntime CoreML
error. Claude pinned it to `CPUExecutionProvider` in `store.py` — same model,
same vectors — and noted it in the Milestone 1 commit.)

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

Run with `python run_eval.py --label before` (three runs per question, response
cache off), then rolled up into one row per criterion with
`python criteria_check.py results/run_2026-10-06_1704_before.md`. Both the
per-question log and the scorer were committed before this run
(`scorer.py::judge`, `criteria_check.py::main`) so the counting rules were
fixed before any answer existed. Evidence: `results/run_2026-10-06_1704_before.md`.

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. Retrieved chunk contains the answer | 4 of 5 | 5/5 | 5/5 | 5/5 | MET |
| 2. Every answer names a source | 5 of 5 | 5/5 | 5/5 | 5/5 | MET |
| 3. Gate stops out-of-corpus questions | 4 of 5 | 5/5 | 5/5 | 5/5 | MET |
| 4. Rank-1 chunk contains the answer | 3 of 5 | 4/5 | 4/5 | 4/5 | MET |
| 5. Cited file is in the answer key | 4 of 5 | 5/5 | 5/5 | 5/5 | MET |

Criteria 1, 3 and 4 depend only on retrieval and the gate, which are
deterministic, so one measurement goes in all three columns. Criteria 2 and 5
depend on the generated answer and were counted separately per run. The answers
did change between runs (question 1 cited one file in runs 1 and 3 and two in
run 2; question 2 cited three files in run 1 and one in runs 2 and 3), which is
how I know the cache really was off.

How each was counted (fixed in `criteria_check.py` before the run):
criterion 1 = any of the top 5 chunks contains the question's `expects` phrase;
criterion 4 = the rank-1 chunk does; criterion 2 = the answer contains a `.md`
filename; criterion 5 = every filename on the answer's last `Source:` line is
in that question's `answer_in` list, and a missing `Source:` line fails.

### Real output, criterion by criterion

**Criterion 1 and 4** — produced by `criteria_check.py::main`, which calls
`store.py::search` with top-k 5:

```
Retrieval detail (criteria 1 and 4):
  expects at ranks [1, 2]; rank 1 = guide_kestrelford.md#1  | How often do buses run from Brightwater to Kestrelford on weekdays?
  expects at ranks [2, 3, 4]; rank 1 = guide_halden_bay.md#6  | What time should I get to Halden Bay in August if I want a parking space?
  expects at ranks [1, 5]; rank 1 = guide_elder_ness.md#1  | How many times a year does the road to Elder Ness flood?
  expects at ranks [1]; rank 1 = guide_accessibility.md#1  | Which town in the region is easiest to visit with limited mobility?
  expects at ranks [1]; rank 1 = guide_accessibility.md#9  | Where is the nearest full hospital in the region?
```

The one rank-1 miss, from `python app.py retrieve` (`app.py::cmd_retrieve`):

```
Question: What time should I get to Halden Bay in August if I want a parking space?

#   distance   source                           preview
1   0.2584     guide_halden_bay.md              Halden Bay — When to go  June and September are the ...
2   0.2822     guide_halden_bay.md              Halden Bay — Getting there  The coast road is the on...
3   0.2876     guide_seasons.md                 When to visit the region — Summer, June to August  J...
4   0.3740     guide_regional_transport.md      Getting around the region — Driving  Roads are good ...
5   0.3962     guide_halden_bay.md              Halden Bay — Where to stay  Almost entirely holiday ...

Gate: best distance 0.258 is under the 0.61 cutoff
```

**Criterion 2 and 5** — run 2, produced by `run_eval.py::run_once` →
`generate.py::answer_from_chunks`:

```
Q: How often do buses run from Brightwater to Kestrelford on weekdays?
Buses run from Brightwater to Kestrelford roughly hourly on weekdays (guide_kestrelford.md). Similarly, the regional transport guide notes that the Kestrelford service is hourly on weekdays (guide_regional_transport.md).
Source: guide_kestrelford.md, guide_regional_transport.md

Q: What time should I get to Halden Bay in August if I want a parking space?
To get a parking space in Halden Bay in August, you should arrive before 10am, or you will need to plan to use the overflow lot.
Source: guide_seasons.md

Q: How many times a year does the road to Elder Ness flood?
The single road to Elder Ness floods roughly six times a year at the highest spring tides, for about two hours either side of high water.
Source: guide_elder_ness.md, guide_walking.md

Q: Which town in the region is easiest to visit with limited mobility?
Thornby Wells is the easiest town in the region for visitors with limited mobility because it is flat, compact, and everything is within three minutes of everything else.
Source: guide_accessibility.md

Q: Where is the nearest full hospital in the region?
The nearest full hospital is located in Marchwood.
Source: guide_accessibility.md
```

**Criterion 3** — produced by `run_eval.py::check_out_of_scope`, cutoff 0.61:

```
| Out-of-scope question | Best distance | Gate |
|---|---|---|
| What is the capital of Mongolia? | 0.810 | refused |
| How do I change the oil in a diesel engine? | 0.881 | refused |
| Who won the 1994 World Cup? | 0.969 | refused |
| What is the recommended dosage of ibuprofen for a headache? | 0.835 | refused |
| How do I write a for loop in Rust? | 0.861 | refused |
```

## Verdicts

Against the targets in criteria.md as written in unit 1. No criterion was
revised: each one could be measured the same way every time with the rules in
`criteria_check.py`, and the brief only allows a revision when the measurement
is broken, not when the result is inconvenient — in either direction.

| # | Criterion | Verdict | How I decided |
|---|---|---|---|
| 1 | Retrieved chunk contains the answer (4 of 5) | MET | 5/5 in every run. Every question had its `expects` phrase in the top 5; I also read each of those chunks to make sure the phrase was the actual answer and not a passing mention (for question 4 the only top-5 chunk naming Thornby Wells is the one that calls it the easiest town). |
| 2 | Every answer names a source (5 of 5) | MET | 15 of 15 answers ended with a `Source:` line naming a real file. Not close — but also not much of a test, because the prompt now demands that line. It measures whether the model follows a format rule, which it did every time. |
| 3 | Gate stops out-of-corpus questions (4 of 5) | MET | Refused 5 of 5; the closest one (Mongolia) was 0.810 against a 0.61 cutoff. The two I worried about in unit 1, ibuprofen and the diesel engine, came in at 0.835 and 0.881. |
| 4 | Rank-1 chunk contains the answer (3 of 5) | MET | 4/5, every run. The miss is question 2: rank 1 is "Halden Bay — When to go", which talks about August and "the parking problem" but never says 10am; the 10am chunks are at ranks 2–4. It's on topic, just not the chunk with the number. I predicted in unit 1 that question 2 or 4 would be the one to miss; it was question 2. |
| 5 | Cited file is in the answer key (4 of 5) | MET | 15 of 15. The cited files varied between runs (question 2 cited three files in run 1 and one in runs 2 and 3) but every file cited was one that actually states the fact. No answer cited a town guide the fact isn't in. |

**The honest read: these targets were set too safely.** Every criterion
cleared with room to spare, on all three runs, which the brief warns usually
means the criteria were safe rather than the system excellent. Arguing the
opposite verdict as hard as I can: criteria 1 and 4 only look good because my
five questions each contain a word only a few chunks share ("flood",
"parking", "hospital", "mobility"), or in question 1's case two town names at
once. I chose those questions
and that's the problem — they test retrieval on its easiest kind of question.
I already had evidence of that in unit 1: "how do I get to Kestrelford?" failed
retrieval, and it isn't in my test set. The diagnosis below goes after it.

## Diagnoses

**No criterion was missed, so there is no miss to diagnose in the strict
sense.** Per the brief, here is what I'd tighten. Then a diagnosis of the one
near-miss inside the test, and of the failure I already knew about outside it,
since that's where my improvement points.

**What I'd tighten, and to what.** Criterion 4 to 4 of 5 — it hit exactly 4/5
on every run, so 3 was a target I couldn't miss. Criterion 2 I'd replace
outright: once the prompt demands a `Source:` line, "names a source" tests
format-following, and criterion 5 already tests the part that matters. But the
bigger problem is the question set, not the numbers (see Verdicts): criteria 1
and 4 should be measured on questions that don't hand retrieval a rare keyword.

### Near-miss: criterion 4, question 2 (rank 1 doesn't contain "10am")

- **Stage:** retrieval, working from the embeddings as designed.
- **Mechanism:** the question's distinctive words are "Halden Bay", "August"
  and "parking". "Halden Bay — When to go" contains all three ("July and
  August are busy enough that the parking problem becomes the defining feature
  of the visit") and wins at 0.258. The chunks with the actual answer, "fill by
  10am" / "arrive before 10am", rank 2–4 at 0.282–0.374. An embedding captures
  what a chunk is *about*, and a time like "10am" carries almost no weight in
  that. It cost nothing here: all three chunks with 10am were in the top 5, and
  generation found it in 3 of 3 runs.

### The failure outside my test: "how do I get to Kestrelford?"

In unit 1 this answered *"the documents do not provide specific instructions
on how to travel there"*. I blamed the `Kestrelford — ...` prefix on every
chunk, guessing the town name drowned out the topic.

**Is it one question or a pattern?** I asked the same short question for all
9 town guides × all 6 standard sections, 54 questions, retrieval only
(`tools/probe_sections.py`, written for this diagnosis after the before-run and
not part of the criteria test). Where the one chunk that answers each
question landed:

| Section asked about | Right chunk at rank 1 | Right chunk in top 5 |
|---|---|---|
| Getting there ("How do I get to X?") | 2/9 | **3/9** |
| Getting around | 4/9 | 9/9 |
| Eat and drink | 8/9 | 9/9 |
| What to see | 0/9 | 8/9 |
| Where to stay | 9/9 | 9/9 |
| When to go | 9/9 | 9/9 |
| **All 54** | 32/54 | 47/54 |

That rules out my unit 1 explanation. If the town prefix drowned out every
topic, "Where to stay" and "When to go" would fail too, and they're 9/9. It's
one section type: "Getting there" misses the top 5 in 6 of 9 towns, usually at
rank 7–9, losing to every other chunk from the same town.

**Three possible causes, one per stage**, and what the evidence says:

1. *Retrieval — top-k is too small.* The right chunk is at rank 7–9, so a
   top-k of 8 would catch most of them. True, but it's a symptom: it doesn't
   say why this one section sinks to the bottom of its own town.
2. *Embedding — MiniLM can't connect "get to" with "Getting there".* If that
   were the cause, "How do I get around X?" would fail the same way; it's in
   the top 5 for 9/9.
3. *Chunking — the chunk is mostly about other places.* This is the one. A
   "Getting there" section describes the route *from* somewhere else, so its
   body is full of other towns, and its heading "there" is a dangling
   reference to a town the body never names. Counted across the 9 town guides:

   | Section | Other towns named per chunk | Own town named in body |
   |---|---|---|
   | Getting there | **1.1** | 0.0 |
   | Overview | 0.2 | 1.0 |
   | every other section | 0.0–0.1 | 0.0–0.1 |

   In "How do I get to X?" the only content word is X. Every X chunk shares
   "X — " in its prefix, so they tie on that, and the one whose body pulls
   hardest toward *other* towns comes last. Thornby Wells' "Getting there"
   ("On the Marchwood line, 25 minutes from the hub") ranked 9th for "How do I
   get to **Marchwood**?" — closer to the town it mentions than the one it's
   about.

**Stage: chunking. Mechanism: the section that answers "how do I get to X"
is the one section whose body is about places other than X, and the only
thing tying it to X is a heading that says "there".** One problem, not six
questions.

Before picking a fix I costed out three candidates on retrieval alone, no
model calls, with the shipped system untouched (`tools/compare_candidates.py`).
"Held-out" means 18 more getting-there questions in wording I didn't use while
diagnosing ("What's the best way to reach X?", "Is there a train or bus to X?").

| Candidate | 54 probes: rank 1 / in context | "How do I get to X?": in context | Held-out: rank 1 / in context |
|---|---|---|---|
| baseline (dense, top-5) | 32 / 47 | 3/9 | 5 / 13 of 18 |
| (a) hybrid BM25 + dense, top-5 | 34 / 45 | **0/9** | 4 / 8 of 18 |
| (b) dense, top-8 | 32 / 53 | 8/9 | 5 / 18 of 18 |
| (c) resolve the heading, top-5 | 31 / 51 | 7/9 | **9** / 16 of 18 |

Hybrid search made the target failure *worse*: BM25 sees "get", not "getting",
and the town name scores the same on every chunk from that town, so keyword
matching has nothing to separate them with. That was the option I'd have
picked by default ("names and exact terms"), and it was wrong for this corpus.

## The Improvement

**What I changed:** one function in the chunking stage. `chunker.py::_resolve_heading`,
called from `chunker.py::split_documents`, replaces the word "there" in a
section heading with "to <guide title>". In this corpus that touches exactly
the nine "Getting there" headings: `Kestrelford — Getting there` became
`Kestrelford — Getting to Kestrelford`. Same 90 chunks, same bodies, same
sizes; nothing else in the pipeline changed (top-k 5, cutoff 0.61, same prompt,
same model). Re-indexed with `python app.py index`.

**Why I picked it:** the diagnosis put the "how do I get to X?" failure at the
chunking stage — the one section that answers it has a body about other towns
and a heading that only says "there" — and this is the change that goes at
that mechanism directly. It's the same rule my unit 1 chunker was built on
(a chunk has to make sense pulled out on its own), applied to a reference I
missed. Top-k 8 scored better on getting the chunk into context (8/9 vs 7/9)
and I didn't pick it: it leaves the chunk at rank 7–8 and widens every
question's prompt by three chunks of mostly same-town noise to fix one section
type. Hybrid search I ruled out because it measured worse (0/9).

### Run Log — After

`python run_eval.py --label after`, rolled up with
`python criteria_check.py results/run_2026-10-06_1710_after.md`. Evidence:
`results/run_2026-10-06_1710_after.md`.

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. Retrieved chunk contains the answer | 4 of 5 | 5/5 | 5/5 | 5/5 | MET |
| 2. Every answer names a source | 5 of 5 | 5/5 | 5/5 | 5/5 | MET |
| 3. Gate stops out-of-corpus questions | 4 of 5 | 5/5 | 5/5 | 5/5 | MET |
| 4. Rank-1 chunk contains the answer | 3 of 5 | 4/5 | 4/5 | 4/5 | MET |
| 5. Cited file is in the answer key | 4 of 5 | 5/5 | 5/5 | 5/5 | MET |

Side by side:

| Criterion | Before (runs 1/2/3) | After (runs 1/2/3) |
|---|---|---|
| 1 | 5/5 · 5/5 · 5/5 | 5/5 · 5/5 · 5/5 |
| 2 | 5/5 · 5/5 · 5/5 | 5/5 · 5/5 · 5/5 |
| 3 | 5/5 | 5/5 |
| 4 | 4/5 · 4/5 · 4/5 | 4/5 · 4/5 · 4/5 |
| 5 | 5/5 · 5/5 · 5/5 | 5/5 · 5/5 · 5/5 |

Best distances that moved: question 1 went 0.208 → 0.219 (still the
Kestrelford getting-there chunk at rank 1), question 3 went 0.282 → 0.252
(the Elder Ness getting-there chunk got closer), and the diesel-engine
question went 0.881 → 0.884. Everything else is identical to three decimals.

Because the five-question test can't see the failure this was aimed at, the
same retrieval-only measurements from the diagnosis, re-run on the shipped
system (`tools/probe_sections.py`, plus the held-out wordings):

| Measure | Before | After |
|---|---|---|
| "How do I get to X?" — right chunk in top 5 | 3/9 | **7/9** |
| "How do I get to X?" — right chunk at rank 1 | 2/9 | 2/9 |
| Held-out wordings — right chunk in top 5 | 13/18 | **16/18** |
| Held-out wordings — right chunk at rank 1 | 5/18 | **9/18** |
| All 54 section probes — in top 5 | 47/54 | 51/54 |
| All 54 section probes — at rank 1 | 32/54 | **31/54** |
| "Getting around" probes — at rank 1 | 4/9 | **3/9** |

Real output on a held-out question after the change (`app.py::cmd_ask`;
the getting-there chunk was at rank 5, inside the context):

```
$ python app.py ask "What's the best way to reach Givens Mill?"
  (best distance 0.385, cutoff 0.61)

The documents do not specify what the "best" way to reach Givens Mill is; they only state that you can drive (taking 20 minutes) or take one of the four weekday buses from Brightwater, noting there is no station and no bus on Sundays.

Source: guide_givens_mill.md
```

And on the question that started all this — still failing:

```
$ python app.py ask "how do I get to Kestrelford?"
  (best distance 0.321, cutoff 0.61)

Based on the provided documents, Kestrelford is located an hour inland from Brightwater. However, the documents do not provide specific instructions on how to travel there.

Source: guide_kestrelford.md
```

**Did it help?** Partly, and I can say exactly where. On my five-question
test it changed nothing — every criterion was met before and after, with the
same counts — which tells me it broke nothing, and also that my test can't
see this kind of failure at all. On the failure it was aimed at, it more than
doubled how often the right chunk reaches the model (3/9 → 7/9 for "How do I
get to X?", 13/18 → 16/18 on wording I never tuned on) and nearly doubled
rank-1 hits on the held-out wording. It did **not** fix the motivating
question: Kestrelford's getting-there chunk went from 0.404 to 0.406 and stayed
at rank 7. And it cost a little elsewhere: one "Getting around" question lost
its rank-1 spot to the new heading: "How do I get around Brightwater?" now ranks "Brightwater — Getting to Brightwater" first (0.309) over "Getting around" (0.330). "Getting to" shares
more words with "get around" than "Getting there" did.

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
