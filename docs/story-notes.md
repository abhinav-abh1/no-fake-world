# Story grouping notes (updated 2026-11-13)

## Definition

Labelling question (step 5A): are two articles mainly about the same news development, even if written separately (or one is a live blog, video page or analysis)? Same topic but a different development counts as different.

Finding: that boundary is fuzzy (see "Why the overlap exists"). Decision: a story is a storyline, meaning one news event plus its direct developments reported within about 3 days (72 hours). Single developments become timeline entries inside a story (step 5D). Broader themes are "topics", handled later.

## Data

- Eight outlets, one feed each. By 10 Nov the last 60 days hold 2,688 articles with vectors and 1,218 stories.
- At labelling time (step 5A): 557 articles (554 independent), 450 of them from 26-30 October; the rest are older items that feeds still listed. Pairs come from each article's 5 nearest neighbours with cosine >= 0.82, sampled evenly across that list. By 4 Nov there were 1,145 articles with vectors in the last 21 days.
- Collection runs from my laptop through a Windows scheduled task (every 30 minutes) and only works while the PC and Docker Desktop are on. On 4 Nov the database container was found stopped. Stories per day dip on days with gaps: 13 stories on 31 Oct (21 articles), 40 on 1 Nov and 32 on 5 Nov, against about 100 on normal days. Outlets with short feeds (Sky 9 items, NPR 10) lose articles during gaps. Real fix: run ingestion on a server.

## Labelling (5A)

- First pass: I labelled 49 of 80 pairs: 3 same story, 46 different. That looked wrong. 11 of the 12 labelled pairs with cosine >= 0.90 were marked different, although in the duplicate session most pairs at that similarity were reports of the same event (Bolsonaro, Israel election, Ebola, Mbappe).
- Cause: I carried over the duplicate-labelling habit, where 0 meant "different report". Story labelling asks "same news development?".
- Fix: I re-judged the pairs labelled 0 from the highest cosine down, with the story rule printed by the tool (`label --kind story --review 0`), then labelled the remaining pairs.
- Second pass: all 80 pairs labelled: 32 same story, 48 different.

## Results: cosine alone

| Threshold | Precision | Recall | F1 | Wrong merges |
|---|---|---|---|---|
| 0.83 | 0.49 | 1.00 | 0.66 | 33 |
| 0.86 | 0.81 | 0.81 | 0.81 | 6 |
| 0.87 | 0.92 | 0.72 | 0.81 | 2 |
| 0.89 | 1.00 | 0.50 | 0.67 | 0 |

- Same-story pairs reach down to 0.8305; different pairs reach up to 0.8861. Between those the score cannot separate them, so cosine alone is not enough. Best F1 is 0.81 (0.86 and 0.87).
- Caveats: one labeller, 80 pairs. "0 wrong merges at 0.89" is 0 mistakes in 16 cases, so the real rate could still be around 1 in 6. Recall only counts pairs that were each other's 5 nearest neighbours at 0.82 or higher.

## Why the overlap exists

I read the mistakes in the overlap band (different pairs >= 0.85, same-story pairs < 0.88):

- About half of the different pairs at 0.85-0.89 are clearly different news: North Korea drones vs Ukraine AI drones, Germany and China vs Merz on world order, the diesel deal vs the climate retreat, Riyadh explosions vs the Jordan airstrike, Macron's protest measures vs the Merz-Macron trade talks, UK-EU talks vs Burnham's India trip.
- The other half are the same storyline but different developments: Israel (Netanyahu analysis vs turnout; pressure on Arab parties vs Golan urging a coalition), Bolsonaro's party recognising Lula's win vs an editorial on his triumph, Spain's election after the train crash vs the crash's safety record.
- Some same-story pairs below 0.88 are broad: Texas Democrats vs Trump on midterm results, the Alaska election dispute pair, Qatar's Emir and Putin vs "Iran war live".
- So the boundary between "same development" and "same storyline" is fuzzy in both directions. This is label granularity, not a missing feature that a second signal would fix.

## Decision

Group at storyline level with average linkage (two groups merge only if their members are similar on average) and a 72-hour window (articles published further apart are never grouped). I did not test single linkage, so I cannot claim average linkage reduced chaining; I chose it in advance.

## Results: grouping (5B)

Method: average linkage on cosine distance, 72-hour window, independent (non-copy) articles. In 5B stories were rebuilt from scratch on every run; 5C-1 replaced that.

`evaluate` on 1,145 articles (21 days); 71 of my 80 labelled pairs usable (30 same story, 41 different):

| Similarity | Stories | Largest | Precision | Recall | F1 |
|---|---|---|---|---|---|
| 0.80 | 232 | 79 | 0.66 | 0.83 | 0.74 |
| 0.83 | 466 | 62 | 0.77 | 0.80 | 0.79 |
| 0.84 | 530 | 47 | 0.80 | 0.80 | 0.80 |
| 0.85 | 594 | 36 | 0.88 | 0.70 | 0.78 |
| 0.86 | 655 | 30 | 0.90 | 0.63 | 0.75 |
| 0.87 | 713 | 28 | 0.94 | 0.53 | 0.68 |
| 0.88 | 759 | 17 | 1.00 | 0.40 | 0.57 |

- Chosen similarity: 0.85 (precision 0.88, recall 0.70). Rows 0.84 to 0.86 differ by only 2 or 3 pairs, which is inside the noise of 71 labels, so I did not tune further. I prefer precision, because a wrong merge puts two events into one story.
- `group_run` at 0.85 on the last 7 days: 503 stories from 996 articles, largest 54, 342 singletons (68% of stories, 34% of articles).

What I read (top stories by number of outlets, all with 6 or 7 outlets):

- Fridge cyberattacks across Europe (17 articles), Russian strikes on a Ukraine aid centre (9), Netanyahu bloc after the Israel election (19), Spain train crash (14), US strikes on Qeshm Island (13), Binance hack (10), Bolsonaro in Miami (8): each reads as one storyline.
- Largest story: US midterms, 54 articles, 7 outlets, spanning 56 hours (previews, explainers, live blogs); 70 articles on a later run. Coherent but broad.
- Possible wrong merges: the Binance story includes a feature on how crypto hacks fund North Korea's nuclear programme (loosely related); the Ukraine strikes story includes the hospital and power-plant attacks (a different development of the same wave).
- Singletons sampled: mostly genuine single-outlet news or features. One probably belongs to a story: a sailor killed near the Strait of Hormuz (Iran story).
- Israel election coverage is split by the 72-hour window into election day (27 Oct) and the aftermath (28-30 Oct). This is intended: a timeline will link them (step 5D).

## Checks after 5B (2026-11-06)

- Check A: `group_run` and `evaluate --days 7` on the same 814 articles agree exactly (361 stories, largest 70 at similarity 0.85). The earlier 36 vs 54 gap was different article sets, not a bug. `evaluate --days 7` cannot score my labelled pairs (all from 27-28 Oct); use `--days 14`.
- Check B: stories by number of distinct outlets (7 days, 361 stories, 814 articles):

| Outlets | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 |
|---|---|---|---|---|---|---|---|---|
| Stories | 261 | 53 | 19 | 13 | 6 | 6 | 2 | 1 |
| Articles | 306 | 127 | 69 | 85 | 45 | 80 | 32 | 70 |

  Stories with 3 or more outlets: 47 (381 articles, 47% of articles), about 7 a day. With 2 or more: 100 stories (62% of articles).
- Check C: the 20 singletons closest to a story. About 14 are right (Bangladesh wage board, Binance fake job interviews, US midterms pieces, Israel opposition, Florida jet crash). About 6 are wrong: North Korea missile test vs the Binance story (0.913), a Russian drone near Moscow vs the aid-centre strike (0.890), a German campus protest vs a cost-of-living protest (0.889), India-China vs China-Iran diplomacy (0.887), UK PMQs vs Burnham on the EU (0.886). Wrong and right scores overlap (0.886-0.918), so I will not attach singletons by centroid similarity.
- Large stories contain developments: the largest group is 186 articles at 0.80, 70 at 0.85, 50 at 0.86, 23 at 0.87, 16 at 0.88. The midterms storyline splits into developments at a stricter cut, which is the basis for timeline entries (step 5D).

## 5C-1: stable story ids (2026-11-09)

- `rebuild_recent` regroups only articles from the last 96 hours (72-hour window plus a 24-hour buffer) and the members of stories that are still open. Older stories are frozen: never changed or deleted. A new group keeps the id of an old story when it contains at least half of that story's articles, so a story that grows keeps its id. Copies are kept inside stories.
- Bootstrap with `--since-days 14`: 1,891 articles, 862 stories regrouped (861 kept their ids, 1 created), plus 1 frozen older story: 863 stories back to 25 Oct.
- Stability test: two further runs gave created=0 removed=0 (330 open, 533 frozen), and the ids of the top stories did not change. The scheduled script now ends with `rebuild_run`.
- Seen: `article_count` includes copies (a DW pair appears twice in a midterms story), and titles are one outlet's headline.
- `group_run` deletes everything and is for experiments only. To apply a new threshold to history, use `rebuild_run --since-days N`.

## 5C-2: independent outlets and edition ranking (2026-11-10)

- New story fields: `independent_outlet_count` (outlets that reprint each other inside a story count once, using the cross-outlet copy flags from dedup) and `original_count` (articles that are not copies).
- Publication rule: at least 3 independent outlets. In the last 7 days, of 599 stories: 412 have 1 independent outlet, 94 have 2, and 93 have 3 or more (31 with 3, 23 with 4, 19 with 5, 9 with 6, 10 with 7, 1 with 8), about 13 edition candidates a day.
- Only 3 stories have outlets merged by a cross-outlet copy (Pope Leo 6 to 5, air traffic 7 to 6, California tax 2 to 1), so the merge is rare and changes few results, but it keeps copy-heavy stories from passing the gate. My first count (9 of 938 stories) was wrong: 6 stories older than 14 days kept `independent_outlet_count` 0 from the migration default. Backfilled with `rebuild_run --since-days 60`; a check for `independent_outlet_count = 0` then returned 0 rows.
- `top_stories` ranks by independent outlets, then originals, then recency. Top of the 72-hour list: Israel (Eisenkot tasked with forming a government; 8 independent of 8 outlets, 24 originals), US midterms (7 of 7, 38 originals), Krakow shooting (7 of 7, 28 originals). Ties at 7 independent outlets are ordered by `original_count`, and only one top-10 story (European air traffic, 6 independent of 7 outlets) has a merged outlet. A 72-hour list lets a three-day-old story outrank a fresher one; a real edition uses a 24-hour window.
- Test isolation lesson: frozen stories are never deleted, so the test database must be emptied between tests. `conftest` did not truncate `stories`, which made a failing test see a leftover story.

## Maintenance rules

- Frozen stories keep derived counts from the last time they were rebuilt. After changing the copy rule or the grouping threshold, run `mark_run`, then `rebuild_run --since-days 60`, then this check (it must return 0):

      SELECT count(*) FROM stories s WHERE s.original_count <> (SELECT count(*) FROM story_articles sa
      JOIN articles a ON a.id = sa.article_id WHERE sa.story_id = s.id AND a.is_duplicate_of_id IS NULL);

- A migration that adds a column with a default needs a backfill and a check that nothing is left at the default.
- After the dedup v3 re-mark (35 near copies), the check returned 0 before and after `rebuild_run --since-days 60` (2,688 articles, 1,218 stories, created=0 removed=0).

## Problems found and plan

1. Fixed in 5C-1: `group_run` deleted all stories on each run (ids changed, history vanished, anything attached to a story would have been deleted with it).
2. Fixed in 5C-2: outlet counts are now independence-aware. Still open: only 8 outlets, and wire reuse is detected only by text similarity.
3. Story titles are one outlet's headline and can carry its framing ("set to upend Trump presidency", "Vile terrorist attack"). Working labels only; the neutral headline comes with the article (Phase 10).
4. Publication rule: implemented (at least 3 independent outlets); stories with 2 are "developing".
5. Singletons stay singletons (see Check C).
6. Stories now keep copies (5C-1), so a results page behind a live blog no longer goes missing from a story. Still open: search hides copies by default; change to grouping before the API (see dedup-notes).
7. The grouping builds an n x n distance matrix, so memory and time grow with the square of the articles. Fine at about 2,700 articles; regroup only recent days when it grows (already the case for the scheduled run).
8. Collection depends on my laptop and is irregular (see Data and data-notes.md); it is biased against outlets with short feeds. Move ingestion to a server.
9. Very large stories need internal structure: cut the same tree at a stricter similarity for developments (5D).

## Next

- 5D: link stories into chains (`parent_story_id`), developments inside large stories, date parsing, and timeline entries for versions whose figures changed.
- Then: move ingestion to a server, the frontend (Phase 6), the LLM layer (Phase 7 onwards).

## Reproduce

    uv run python -m app.dedup.export_pairs --kind story
    uv run python -m app.dedup.label --kind story
    uv run python -m app.dedup.label --kind story --review 0
    uv run python -m app.stories.tune
    uv run python -m app.stories.evaluate --days 14 --errors 0.85
    uv run python -m app.stories.rebuild_run                  # normal scheduled run
    uv run python -m app.stories.rebuild_run --since-days 60  # rebuild history after a rule change
    uv run python -m app.stories.show --top 8
    uv run python -m app.stories.top --hours 24
    uv run python -m app.stories.group_run --threshold 0.85   # experiments only, deletes all stories