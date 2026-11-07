# Search notes (updated 2026-11-03)

## Embeddings
- Model: intfloat/multilingual-e5-small (384 dimensions), run on CPU.
- Timing: first model download 167 s (one time). Embedding 328 articles took 10.3 s (about 32
  articles per second); a later batch of 224 articles took 8.2 s (about 27 per second). Loading the
  model from disk takes 15 to 50 s.
- Scores from this model sit in a narrow high band, so only the ranking matters, not the numbers.

## First look: meaning search only (4 queries)
| Query | Result quality | What I noticed |
|---|---|---|
| who won the Israel election | 10 of 10 on topic | five outlets, varied wording |
| oil deal with Venezuela | 3 good, then drifts to other oil stories | the model weighs "oil" strongly |
| Brazil presidential election result | 10 of 10 on topic | possible wire copy across outlets |
| cost of living and housing | 2 good, rest weak | irrelevant scores overlap with relevant ones |

Problems this showed: a search always returned 10 results even when nothing was relevant,
scores of relevant and irrelevant results overlap, and the same outlet appears several times
(count distinct outlets as independent sources).

## Hybrid search
Method: Postgres full-text (english config, all words must appear) + e5 cosine similarity,
merged with reciprocal rank fusion (k = 60). Copies found by dedup are hidden. A meaning-only
hit must reach a minimum cosine similarity; a keyword hit always counts.

Evaluated on 10 real queries (6 topical, 4 abstract) and 10 off-topic queries, looking at the
keyword, vector and hybrid lists for each.

What I saw:
- Keyword wins on rare names: "Nord Stream sabotage trial" matched exactly one article, the right one.
- Keyword misses word forms: "Mbappe Mao apology" matched 1 article, while the top 5 by meaning
  were all Mbappe stories (likely a stemming mismatch between apology and apologises).
- Vector wins on abstract queries: "disease outbreak spreading in Africa" found the Ebola
  coverage without the word Ebola. But it has a weak tail: for "athletes causing controversy
  abroad" the top hit was right (0.844) and ranks 2 and 3 were only loosely related (a sports
  journalist's case, a Eurovision story).
- Hybrid combined both and returned nothing for off-topic queries.

## No-match threshold
- Best cosine score per query: real queries 0.844 to 0.940; off-topic queries 0.776 to 0.813.
- With only 3 off-topic queries the highest was 0.799 and the threshold was 0.80 (a margin of
  0.001). After adding 7 more off-topic queries the highest rose to 0.813 (hiking trails in the
  Alps). I moved the threshold to 0.83, the middle of the gap between 0.813 and 0.844.
- Result: all 10 off-topic queries return "no good match", all 10 real queries return results.
- Caveat: this is 20 queries on 333 articles, 226 of them from 26-28 October (the rest are older
  items that feeds still listed). More off-topic queries would probably find a score above 0.83,
  so the threshold is a cautious guess, not a guarantee.

## Known problems
- Only The Guardian has full text, so keyword matches on generic words are all Guardian
  articles, and long articles match by accident (text rank 0.000 to 0.001). For example a long
  campaign story appeared for the Israel, Brazil and cost-of-living queries and ranked above
  better meaning matches. Plan: build the keyword index from title and snippet only (small
  migration) when the search API is built.
- Keyword search is English-only (stemming config). Other languages need their own handling.
- A relative cutoff (drop results far below the best score) might remove the weak tail. Not tried.
- The search is a command line tool for now. A web endpoint needs the model inside the API
  container, which is a deployment decision for later.

## Re-check on larger data (2026-11-06)
- Corpus grew from 333 to more than 1,100 articles.
- Off-topic best cosine: 0.787 to 0.816 (the chocolate cake query is highest). Real queries best
  cosine: 0.856 to 0.940. Threshold 0.83 still separates them: 0.014 above the highest off-topic
  score and 0.026 below the lowest real query. All 10 off-topic queries still return "no good match".
- Trend: the highest off-topic score rose from 0.799 (333 articles) to 0.813 and now 0.816,
  because a bigger corpus always has a closer neighbour. A fixed threshold will keep eroding, so
  the off-topic queries should become an automated check that runs as the corpus grows (Phase 12).
  
## Reproduce
    uv run --group ml python -m app.embeddings.search_cli "who won the Israel election"
    uv run --group ml python -m app.embeddings.compare_cli