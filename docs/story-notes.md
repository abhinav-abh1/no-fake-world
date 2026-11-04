# Story grouping notes (updated 2026-11-04)

## Definition
Labelling question (step 5A): are two articles mainly about the same news development, even if
written separately (or one is a live blog, video page or analysis)? Same topic but a different
development counts as different.

Finding: that boundary is fuzzy (see "Why the overlap exists"). Decision: a story is a storyline,
meaning one news event plus its direct developments reported within about 3 days (72 hours).
Single developments become timeline entries inside a story (step 5D). Broader themes are
"topics", handled later.

## Data
- At labelling time: 557 articles (554 independent), 450 of them from 26-30 October; the rest are
  older items that feeds still listed. Pairs come from each article's 5 nearest neighbours with
  cosine >= 0.82, sampled evenly across that list.
- Hourly collection runs through a Windows scheduled task, which only works while the PC and Docker
  Desktop are on. On 4 Nov the database container was found stopped, so collection gaps are
  possible (31 Oct has only 21 articles). By 4 Nov there were 1,145 articles with vectors in the
  last 21 days.

## Labelling
- First pass: I labelled 49 of 80 pairs: 3 same story, 46 different. That looked wrong. 11 of the
  12 labelled pairs with cosine >= 0.90 were marked different, although in the duplicate session
  most pairs at that similarity were reports of the same event (Bolsonaro, Israel election, Ebola,
  Mbappe).
- Cause: I carried over the duplicate-labelling habit, where 0 meant "different report". Story
  labelling asks "same news development?".
- Fix: I re-judged the pairs labelled 0 from the highest cosine down, with the story rule printed
  by the tool (label --kind story --review 0), then labelled the remaining pairs.
- Second pass: all 80 pairs labelled: 32 same story, 48 different.

## Results: cosine alone
| Threshold | Precision | Recall | F1 | Wrong merges |
|---|---|---|---|---|
| 0.83 | 0.49 | 1.00 | 0.66 | 33 |
| 0.86 | 0.81 | 0.81 | 0.81 | 6 |
| 0.87 | 0.92 | 0.72 | 0.81 | 2 |
| 0.89 | 1.00 | 0.50 | 0.67 | 0 |

- Same-story pairs reach down to 0.8305; different pairs reach up to 0.8861. Between those the
  score cannot separate them, so cosine alone is not enough. Best F1 is 0.81 (0.86 and 0.87).
- Caveats: one labeller, 80 pairs. "0 wrong merges at 0.89" is 0 mistakes in 16 cases, so the real
  rate could still be around 1 in 6. Recall only counts pairs that were each other's 5 nearest
  neighbours at 0.82 or higher.

## Why the overlap exists
I read the mistakes in the overlap band (different pairs >= 0.85, same-story pairs < 0.88):
- About half of the different pairs at 0.85-0.89 are clearly different news: North Korea drones vs
  Ukraine AI drones, Germany and China vs Merz on world order, the diesel deal vs the climate
  retreat, Riyadh explosions vs the Jordan airstrike, Macron's protest measures vs the Merz-Macron
  trade talks, UK-EU talks vs Burnham's India trip.
- The other half are the same storyline but different developments: Israel (Netanyahu analysis vs
  turnout; pressure on Arab parties vs Golan urging a coalition), Bolsonaro's party recognising
  Lula's win vs an editorial on his triumph, Spain's election after the train crash vs the crash's
  safety record.
- Some same-story pairs below 0.88 are broad: Texas Democrats vs Trump on midterm results, the
  Alaska election dispute pair, Qatar's Emir and Putin vs "Iran war live".
- So the boundary between "same development" and "same storyline" is fuzzy in both directions.
  This is label granularity, not a missing feature that a second signal would fix.

## Decision
Group at storyline level with average linkage (two groups merge only if their members are similar
on average) and a 72-hour window (articles published further apart are never grouped). I did not
test single linkage, so I cannot claim average linkage reduced chaining; I chose it in advance.

## Results: grouping (5B)
Method: average linkage on cosine distance, 72-hour window, independent (non-copy) articles.
Stories are rebuilt from scratch on every run.

evaluate on 1,145 articles (21 days); 71 of my 80 labelled pairs usable (30 same story, 41 different):

| Similarity | Stories | Largest | Precision | Recall | F1 |
|---|---|---|---|---|---|
| 0.80 | 232 | 79 | 0.66 | 0.83 | 0.74 |
| 0.83 | 466 | 62 | 0.77 | 0.80 | 0.79 |
| 0.84 | 530 | 47 | 0.80 | 0.80 | 0.80 |
| 0.85 | 594 | 36 | 0.88 | 0.70 | 0.78 |
| 0.86 | 655 | 30 | 0.90 | 0.63 | 0.75 |
| 0.87 | 713 | 28 | 0.94 | 0.53 | 0.68 |
| 0.88 | 759 | 17 | 1.00 | 0.40 | 0.57 |

- Chosen similarity: 0.85 (precision 0.88, recall 0.70). Rows 0.84 to 0.86 differ by only 2 or 3
  pairs, which is inside the noise of 71 labels, so I did not tune further. I prefer precision,
  because a wrong merge puts two events into one story.
- group_run at 0.85 on the last 7 days: 503 stories from 996 articles, largest 54, 342 singletons
  (68% of stories, 34% of articles).

What I read (top stories by number of outlets, all with 6 or 7 outlets):
- Fridge cyberattacks across Europe (17 articles), Russian strikes on a Ukraine aid centre (9),
  Netanyahu bloc after the Israel election (19), Spain train crash (14), US strikes on Qeshm Island
  (13), Binance hack (10), Bolsonaro in Miami (8): each reads as one storyline.
- Largest story: US midterms, 54 articles, 7 outlets, spanning 56 hours (previews, explainers, live
  blogs). Coherent but broad.
- Possible wrong merges: the Binance story includes a feature on how crypto hacks fund North
  Korea's nuclear programme (loosely related); the Ukraine strikes story includes the hospital and
  power-plant attacks (a different development of the same wave).
- Singletons sampled: mostly genuine single-outlet news or features. One probably belongs to a
  story: a sailor killed near the Strait of Hormuz (Iran story).
- Israel election coverage is split by the 72-hour window into election day (27 Oct) and the
  aftermath (28-30 Oct). This is intended: a timeline will link them (step 5D).

## To verify
- evaluate (21 days) reported largest group 36 at 0.85, group_run (7 days) reported 54. They ran on
  different article sets minutes apart. Re-run both back to back: <result>.
- Stories with at least 3 outlets: <N> stories covering <N> articles.

## Problems found and plan
1. group_run deletes ALL stories on each run and rebuilds only the last 7 days. Older stories
   disappear, ids change on every run, and anything attached to a story (claims, articles) would be
   deleted with it. Do not schedule group_run. Fix in 5C: stable ids, freeze stories older than the
   window, regroup only recent days.
2. outlet_count counts distinct outlets, not independent confirmations. Only 8 outlets, and several
   reuse wire copy (AP, AFP, Reuters). Needs wire detection before verification (Phase 8).
3. Story titles are one outlet's headline and can carry its framing ("set to upend Trump
   presidency", "Vile terrorist attack"). They are working labels only; the neutral headline is
   written with the article (Phase 10).
4. 68% of stories are singletons. Plan a publication rule (minimum number of outlets) and test
   attaching a singleton to its nearest story when similarity >= 0.82.
5. The method builds an n x n distance matrix, so memory and time grow with the square of the
   articles. Fine at about 1,100; regroup only recent days when it grows.
6. Very large stories (midterms, 54 articles) need internal structure: cut the same tree at a
   stricter similarity to get "developments" for the timeline.

## Next
- 5C: stable story ids, importance ranking by independent outlets and recency, publication rule,
  singleton attach.
- 5D: timelines linking stories over days.

## Reproduce
    uv run python -m app.dedup.export_pairs --kind story
    uv run python -m app.dedup.label --kind story
    uv run python -m app.dedup.label --kind story --review 0
    uv run python -m app.stories.tune
    uv run python -m app.stories.evaluate --days 7 --errors 0.85
    uv run python -m app.stories.group_run --threshold 0.85
    uv run python -m app.stories.show --top 8