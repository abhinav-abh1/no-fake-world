# Duplicate detection notes (2026-10-28)

## Goal
Mark articles that are copies of an earlier article, so a reprinted story counts as one source
when the verifier later counts independent confirmations.

## Method
- A pair is a copy when BOTH hold: cosine similarity of e5 embeddings >= 0.95 AND overlap of
  3-word shingles (Jaccard) >= 0.3. Exact duplicates (same extracted text hash) are marked too.
- The earlier article (by published time, then fetch time) is the original; copies point to the root.

## Labelling
- Definition: copy = the same piece of writing, lightly edited. The same event written
  separately is NOT a copy (those are grouped into stories in Phase 5).
- 60 candidate pairs exported (nearest neighbours with cosine >= 0.90, spread across the range).
  Labelled 53 by hand, skipped 7: 1 copy, 52 different.

## Results
- Result on the full data: exact=0, near=1 (333 articles, 332 independent). I checked the marked
  pair by hand: it is the pair I labelled as a copy. Direction check: the original (14:45 UTC)
  is earlier than the copy (16:52 UTC), as intended.
- Why two signals: among my labelled pairs, cosine >= 0.95 alone flags 3 pairs and only 1 is a
  real copy (precision 0.33). The two false ones (cosines 0.953 and 0.952) have Jaccard 0.03 and
  0.01, so the Jaccard gate removes them. The real copy has cosine 0.978 and Jaccard 0.45.
- Why 0.3: the one true copy has Jaccard 0.45 and the highest "different" pair has 0.08, so 0.3
  sits inside that gap with room on both sides.
- Every setting in the tuner's top-10 table scored 1.00, but that is one example, not proof.
  I did not pick the strictest row (cosine 0.97) because the only copy has cosine 0.978.

## Mistakes and limits
- Mistake I made: I first labelled 3 same-event pairs as copies. Their Jaccard was 0.04-0.06.
  After reading the texts I relabelled them as different reports.
- Limitation: only ONE labelled copy, and it is the same outlet (France 24) reusing its own
  blurb. Cross-outlet wire copy was never validated, so these thresholds are a cautious guess,
  not a measured result.

## Next
- Test comparing body text only (the title lowered the Jaccard of the one true copy).
- Relabel after more data and more full-text sources.

## Reproduce
    uv run python -m app.dedup.export_pairs --max 60
    uv run python -m app.dedup.label
    uv run python -m app.dedup.tune
    uv run python -m app.dedup.mark_run