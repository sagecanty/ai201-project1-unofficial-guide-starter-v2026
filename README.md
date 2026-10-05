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
