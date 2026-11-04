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

## Mistakes and limits
- Mistake I made: I first labelled 3 same-event pairs as copies. Their Jaccard was 0.04-0.06.
  After reading the texts I relabelled them as different reports.
- Precision looks good (every pair the rule marked is a real copy), but I cannot measure recall:
  I only know about copies that were marked or that happened to be in my 53 labelled pairs.
- Only one labelled copy came from my labelling session, and it is the same outlet (France 24)
  reusing its own blurb. The two newer copies are not in the labelled file, so the thresholds were
  not re-tuned on them.
- Copies are judged on titles and opening text, so two articles that start the same and then
  diverge would still be marked. I have not seen this happen.

## Next
- Test comparing body text only (the title lowered the Jaccard of the first true copy).
- Add the new copies and more candidate pairs to the labelled file and re-tune.

## Reproduce
    uv run python -m app.dedup.export_pairs --max 60
    uv run python -m app.dedup.label
    uv run python -m app.dedup.tune
    uv run python -m app.dedup.mark_run