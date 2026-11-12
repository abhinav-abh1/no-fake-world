# Duplicate detection notes (updated 2026-11-13)

## Goal

Find articles that reuse another article's text, for two different purposes:

1. **Independence.** When several outlets cover a story, an outlet that adapted or reprinted another outlet's text is not an independent confirmation. Only links between different outlets matter.
2. **Display.** One outlet often lists the same blurb twice (two headlines, same minute). The later article can be grouped with the first without losing anything.

## Method (rule v3)

A pair is a near copy when ALL of these hold:

- cosine similarity of the e5 embeddings >= 0.95;
- overlap of 3-word shingles (Jaccard) >= 0.3;
- publication times are close: same outlet within 30 minutes, different outlets within 6 hours;
- their figures do not conflict: if both texts give numbers and neither set contains the other (33 vs 22, "six and fifteen" vs "five and a dozen"), the later article is an update, not a copy. A date that appears in only one text is not a conflict.

Exact duplicates (same extracted text hash) are marked too (none so far).

- The text compared is the title plus the opening of the article (extracted text if we have it, otherwise the feed snippet, which is all we have for seven of the eight outlets).
- The earliest article (by published time, then fetch time) is the original; copies point to the root original. See Limits: for updates the later version is the one readers want.
- `is_near_copy` in `mark.py` is the single definition of the rule. Marking, the labelling export and the evaluation all use it.
- Settings: `dedup_min_cosine` 0.95, `dedup_min_jaccard` 0.3, `dedup_same_outlet_minutes` 30, `dedup_cross_outlet_hours` 6.

### Rule history

| Version | Change | Reason |
|---|---|---|
| v1 | cosine >= 0.95 and Jaccard >= 0.3 | Cosine alone flagged 3 labelled pairs and only 1 was a real copy (precision 0.33). The two false ones (cosine 0.953 and 0.952) have Jaccard 0.03 and 0.01. |
| v2 | time gate (same outlet 30 min, other outlets 6 h) | A Hindu live blog and its results page 22 hours later, and an Al Jazeera live blog and an explainer, were being hidden. |
| v3 | figures-conflict gate | Same-outlet updates with changed figures (Yemen "33 killed" vs "22 killed", Krakow "6 killed" vs "5 killed") were being hidden. |

Thresholds were fitted by eye to a small number of pairs. They are hypotheses, not measured results. Errors are not symmetric: a missed copy leaves one extra article, a false merge hides a real one.

- Why 0.3 for Jaccard: the first true copy has Jaccard 0.45 and the highest "different" pair had 0.08, so 0.3 sits inside that gap.
- Why not cosine 0.97: every setting in the tuner's top-10 table scored 1.00, but that was one example, not proof. The only labelled copy at that time had cosine 0.978, so the strictest row was not chosen.

## Labelling

- 96 labelled pairs (49 same outlet, 47 different outlets), taken from nearest-neighbour pairs with cosine >= 0.90 and from the pairs the rule marked at the time. The first export was 60 candidate pairs spread across the cosine range (53 labelled, 7 skipped).
- Rule, printed by the tool for every pair:
  - Same outlet: 1 only if hiding the later article loses nothing (same facts, nothing added).
  - Different outlet: 1 if one is adapted or reprinted from the other (shared origin), even if it adds details.
  - Everything else is 0: a different report of the same event, a version that changes or adds a fact, a preview vs the report.
- The pairs were mostly selected by the rule itself, so precision flatters it and recall is only measured on the labelled pairs.

## Results over time

- **First run (333 articles):** 1 copy marked, the France 24 blurb pair I had labelled. The original (14:45 UTC) is earlier than the copy (16:52 UTC), as intended. That pair is 2.1 hours apart within one outlet, so under the time gate (v2 onward) it is no longer marked.
- **Second run (557 articles, 554 independent):** 3 copies, all read by hand, all real: the France 24 blurb pair, a France 24 programme listed twice, and a Hindu article whose opening sentence matches another with tiny edits. The programme pair has no extracted text, which is why the exact-hash check found nothing (exact=0) and the near rule caught it.
- **Third run (about 1,500 articles):** 18 flagged (DW 10, France 24 5, The Hindu 2, Al Jazeera 1; 17 same outlet, 1 different outlet).
  - 13 were re-listings: one outlet, the same blurb under two headlines, 0 to 14 minutes apart (mostly DW and France 24).
  - 4 were same-outlet pages hours apart: the first France 24 pair (2.1 h), a Hindu rewrite of an update (4.6 h), an Al Jazeera live blog and an explainer (2.7 h), and a Hindu live blog "Voting begins" against the "Full list of winners" page 22 hours later.
  - 1 was a real cross-outlet reuse: the California billionaire-tax pair, 3.7 hours apart.
  - Two flagged pairs were unsafe to hide (the Hindu live blog vs results page and the Al Jazeera live blog vs explainer). Precision on the 18 flagged pairs was 16 of 18 (0.89). Cosine and Jaccard cannot separate them from true copies because their text is almost the same.
- **v2 time gate:** exact=0, near=20 on the corpus at the time. Every flagged same-outlet pair is within 30 minutes and every cross-outlet pair within 6 hours (checked by query). The Hindu results page and the Al Jazeera live blog are no longer hidden.
- **Audit of 19 new pairs (v3):** the labelling export ignored the time gate; two identical pairs had been mislabelled; and same-outlet updates with changed figures were being hidden. The export, marking and evaluation now share `is_near_copy`, and the figures-conflict gate keeps updates visible.
- **Current state (v3):** `mark_run` gives exact=0, near=35 on the current corpus (it has grown, so this is not comparable with earlier counts). `rebuild_run --since-days 60` gave candidates=2688, stories=1218, kept=1218, created=0, removed=0, frozen=0. The stale-story check (stories whose `original_count` disagrees with the non-duplicate article count) returned 0 before and after the rebuild. Tests (41), ruff and mypy pass.

## Two meanings of "copy"

My first evaluation of the live rule on the 96 pairs read: marked 28, tp 19, fp 9, fn 4 (precision 0.68, recall 0.83). It was misleading, because my labels mixed two questions: shared origin (independence) and harmless to hide (display). I reviewed the disagreements under the two-question rule above. The rule did not change, the labels did: six labels changed (five 0 to 1, one 1 to 0).

- **0 to 1, two same-outlet re-listings:** the DW "Democrats flip House and Senate" pair and the Wawira Njiru pair. Same facts, reworded, nothing lost by hiding the later one.
- **0 to 1, three cross-outlet reprints:** air traffic (France 24 plus a shorter copy of its text, 1.2 h apart), Pope Leo (5.6 h apart) and the California billionaire tax (3.7 h apart). These share an origin, so they are correct for independence.
- **1 to 0, one preview vs report:** Mélenchon. The earlier article says he is "set to" announce the programme, the later one says he announced it, so hiding the later one loses the news.

Evaluation of the live rule on the relabelled pairs:

| | Labelled | Marked | tp | fp | fn | tn | Precision | Recall |
|---|---|---|---|---|---|---|---|---|
| Same outlet | 49 | 25 | 21 | 4 | 3 | 21 | 0.84 | 0.88 |
| Other outlet | 47 | 3 | 3 | 0 | 0 | 44 | 1.00 | 1.00 |
| Combined | 96 | 28 | 24 | 4 | 3 | 65 | 0.86 | 0.89 |

- The rule marked only 3 of 47 cross-outlet pairs, and all 3 are real shared-origin pairs, so it does not over-merge different reports from different outlets.
- **Remaining false merges (4, all same outlet, 0.0 h apart):**
  - Krakow "At least five killed" vs "Poland: At least 5 killed" (cosine 0.997) and "At least 5 killed in Polish city" vs "Poland: At least 5 killed" (0.989). The versions differ in small details (the injury count wording, "from a car" vs "in a market square").
  - Krakow "At least 6 killed" vs "Gunman kills 6" (0.979). The later version adds the shooter's ideology, so this is a real false merge. The figures gate does not help because both versions give the same figures.
  - Iran "Iranians face looming war threat" vs "For people in Iran, a constant threat of war" (0.972). The later version changes "ordinary people" to "most people" and adds "US-led".
- **Remaining missed copies (3, all same outlet, beyond the 30-minute gate):** France debt blurb re-listed 17.6 h later (cosine 0.996), a Hindu rewritten lead 4.6 h later (0.974), and the US midterms live blog vs "When will we know" explainer, 2.7 h apart (0.974). The gate refuses these on purpose: hiding a later page is riskier than leaving an extra article. The last pair is labelled 1 because the compared snippets are identical, but the live blog page itself is not the same as the explainer (see Limits).
- The Krakow "6 killed" vs "5 killed" pair no longer appears as a false merge: the figures-conflict gate keeps it visible.

## Limits

- One labeller, and a sample selected by the rule. Only 3 cross-outlet reprints are labelled as positives, so the cross-outlet precision and recall of 1.00 rest on 3 pairs and say little about recall for independence.
- Labels were revised after I saw where the rule disagreed with them. Part of the improvement from 0.68 to 0.84 precision on same-outlet pairs reflects clearer labelling, not a better rule.
- For seven of eight outlets the comparison uses a one or two sentence snippet. Two pages that share a lead sentence can look like copies (the live blog vs explainer case), and a copy that differs later in the text is missed.
- "Original = earliest" is wrong for updates: the later version is the one readers want.
- Most flagged pairs are one outlet re-listing its own text, which does not change how many different outlets cover a story. Only cross-outlet pairs affect independence.
- Search currently hides copies by default. Policy for the API: group near copies for display, do not hide them, so a version that adds a fact stays visible.

## Mistakes made

- The 7 pairs I skipped in the first session were labelled 1 by mistake, because I answered the story question instead of the copy question. The tuner showed recall 0.72 (7 "missed copies"), which exposed it. I relabelled them 0.
- In the audit, two identical pairs were labelled 0 by mistake and were relabelled 1.
- The first evaluation mixed the independence and display questions, which made the rule look worse than it was (see Two meanings of "copy").

## Next

- Export more cross-outlet candidate pairs as the corpus grows, label them with the rule above, and re-measure independence recall.
- Use cross-outlet copy links to compute independent outlets for a story (step 5C).
- Compare body text for outlets with full text (only The Guardian so far). The title lowered the Jaccard of the first true copy, so body-only comparison is worth testing.
- Replace "hide" with "group" when the search API is built.

## Reproduce

    uv run python -m app.dedup.export_pairs --max 60      # candidate pairs for labelling
    uv run python -m app.dedup.export_pairs --marked      # pairs the live rule marks
    uv run python -m app.dedup.label                      # unlabelled pairs, rule shown for each
    uv run python -m app.dedup.label --review 0 --contains "text"
    uv run python -m app.dedup.label_changes              # what changed since the last commit
    uv run python -m app.dedup.tune                       # threshold table
    uv run python -m app.dedup.evaluate                   # live rule, same vs other outlet
    uv run python -m app.dedup.mark_run
    uv run python -m app.stories.rebuild_run --since-days 60   # after any rule change