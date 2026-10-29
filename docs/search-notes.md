# Search notes (2026-10-28)

Model: intfloat/multilingual-e5-small (384 dimensions), 328 articles.
Timing: model load 167 s (first download only), embedding 328 articles in 10.3 s.

| Query | Result quality | What I noticed |
|---|---|---|
| who won the Israel election | 10/10 on topic | five outlets, varied wording |
| oil deal with Venezuela | 3 good, then drifts to other oil stories | model weighs "oil" strongly |
| Brazil presidential election result | 10/10 on topic | possible wire copy across outlets |
| cost of living and housing | 2 good, rest weak | irrelevant scores overlap with relevant ones |

## Problems to solve
- A search always returns 10 results, even when nothing relevant exists.
- Scores of relevant and irrelevant results overlap, so a plain threshold will not work.
- The same outlet appears several times: count distinct outlets as independent sources.
- Possible near-duplicate wire stories: handle in dedup (Phase 4B).


## Hybrid search (2026-10-28)
- Keyword: Postgres full-text (english config, stemming); all words must appear.
- Vector: e5 cosine similarity.
- Fusion: reciprocal rank fusion (k=60); no-match rule: meaning-only hits need cosine >= <your value>.
- Compared on <N> queries. Where keyword won: <...>. Where vector won: <...>. Where hybrid helped: <...>.
- Off-topic queries (<3>): best vector scores <values>; topical queries: <range>. Threshold chosen: <value>.
- Limits: English-only keyword search; threshold tuned on <N> queries; copies hidden via dedup marks.