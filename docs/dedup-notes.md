# Duplicate detection notes (updated 2026-11-03)

## Goal
Mark articles that are copies of an earlier article, so a reprinted story counts as one source
when the verifier later counts independent confirmations.

## Method
- A pair is a copy when BOTH hold: cosine similarity of e5 embeddings >= 0.95 AND overlap of
  3-word shingles (Jaccard) >= 0.3. Exact duplicates (same extracted text hash) are marked too.
- The text compared is the title plus the opening of the article (extracted text if we have it,
  otherwise the feed snippet). For sources without extracted text, only the snippet is compared.
- The earlier article (by published time, then fetch time) is the original; copies point to the root.

## Labelling
- Definition: copy = the same piece of writing, lightly edited. The same event written
  separately is NOT a copy (those are grouped into stories in Phase 5).
- 60 candidate pairs exported (nearest neighbours with cosine >= 0.90, spread across the range).
  Labelled 53 by hand, skipped 7: 1 copy, 52 different.

## Results
- First run (333 articles): exact=0, near=1. The marked pair was the one I had labelled as a copy.
  Direction check: the original (14:45 UTC) is earlier than the copy (16:52 UTC), as intended.
- Second run (557 articles, 554 independent): exact=0, near=3. I read all three marked pairs:
  1. The France 24 blurb pair I had labelled (same text, different correspondent name).
  2. A France 24 programme listed twice, with identical title and identical opening text.
  3. A Hindu article whose opening sentence matches another article with only tiny edits
     ("three quarters" / "three-quarters", "Mr. Netanyahu" / "Benjamin Netanyahu", "still short").
  All three are the same writing in the text I compared, so no false merges on the new data
  (3 of 3 checked by hand).
- Why exact=0: the text hash exists only for articles whose full text was extracted. Pair 2 has
  no extracted text, so the near rule caught it.
- Why two signals: among my labelled pairs, cosine >= 0.95 alone flags 3 pairs and only 1 is a
  real copy (precision 0.33). The two false ones (cosines 0.953 and 0.952) have Jaccard 0.03 and
  0.01, so the Jaccard gate removes them. The first real copy has cosine 0.978 and Jaccard 0.45.
- Why 0.3: the first true copy has Jaccard 0.45 and the highest "different" pair has 0.08, so
  0.3 sits inside that gap with room on both sides.
- Every setting in the tuner's top-10 table scored 1.00, but that was one example, not proof.
  I did not pick the strictest row (cosine 0.97) because the only labelled copy has cosine 0.978.

## Third run (2026-11-06)
- 18 pairs flagged on about 1,500 articles (3 on 557 articles earlier). By copy source: DW 10,
  France 24 5, The Hindu 2, Al Jazeera 1. 17 are the same outlet, 1 is a different outlet.
- 13 are re-listings: the same outlet publishes the same blurb under two headlines, 0 to 14 minutes
  apart (DW and France 24). Reading them, the text is identical or nearly so.
- 4 are the same outlet hours apart: the first France 24 pair I labelled (2.1 h, two videos with one
  blurb), a Hindu rewrite of an update (4.6 h), an Al Jazeera live blog and an explainer (2.7 h),
  and a Hindu live blog "Voting begins" against the "Full list of winners" page 22 hours later.
- 1 is a real cross-outlet reuse: the California billionaire-tax pair shares an identical sentence
  across two outlets, 3.7 hours apart.
- Two flagged pairs are unsafe to hide: the Hindu live blog vs results page (a lead paragraph
  edited a day later) and the Al Jazeera live blog vs explainer (one shared sentence). Hiding the
  later page would lose the results page. I labelled both 0, so precision on the 18 flagged pairs
  is 16 of 18 (0.89). Cosine and Jaccard cannot separate them from the true copies, because their
  text is almost the same.
- Mistake I made: the 7 pairs I had skipped in the first session were labelled 1 by mistake,
  because I answered the story question instead of the copy question. The tuner showed recall 0.72
  (7 "missed copies"), which exposed it. I relabelled them 0.
- Caveat: the 18 pairs were selected by the rule itself, so recall is not measured.

## Mistakes and limits
- Precision is 16 of 18 on the flagged pairs. I cannot measure recall: I only know about copies
  that were flagged or that happened to be in my labelled pairs.
- Most flagged pairs are one outlet re-listing its own text, which does not change how many
  different outlets cover a story. Only the cross-outlet pair affects independence.
- Copies are judged on titles and opening text (a feed snippet for seven of the eight outlets), so
  a shared lead sentence between different pages is enough to trigger the rule.
- Which article is "the original" is simply the earliest. For an updated page, the later version
  is the one readers want.

## Next
- Dedup v2: only mark near copies that are close in time (same outlet within 30 minutes, other
  outlets within 6 hours). This is fitted by eye to 18 pairs, so it is a hypothesis. Errors are
  not symmetric: a missed copy leaves one extra article, a false merge hides a real one.
- Use cross-outlet copy links to compute independent outlets for a story (step 5C).
- Compare body text only (the title lowered the Jaccard of the first true copy).
## Reproduce
    uv run python -m app.dedup.export_pairs --max 60
    uv run python -m app.dedup.label
    uv run python -m app.dedup.tune
    uv run python -m app.dedup.mark_run