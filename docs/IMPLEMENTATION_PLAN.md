# No Fake World — Full Implementation Plan

> A step-by-step, build-from-scratch guide. Written so that anyone (including you, six months from now) can open this file, find the last finished step, and continue.

**Last updated:** 24 October 2026 · **Suggested start:** Monday 26 October 2026 · **Suggested launch:** end of January 2027 (dates are targets, not promises)

---

## 0. How to use this document

1. Work **one phase at a time**. Do not start Phase N+1 until every box in Phase N's **"Done when"** list is ticked.
2. Tick boxes (`- [x]`) in this file as you go, and write the date next to each finished phase in the **Status board** below.
3. If you stop for days or weeks: go to **Section 18 (Resume protocol)**. It takes 20 minutes to get back in.
4. Every phase has the same shape: **Goal → Why → Learn first → Steps → Done when → If you get stuck.**
5. Do not skip "Learn first". The goal of this project is to **understand** every part, not only to make it run.
6. Free tiers, model names, prices and limits change often. Anything marked **(verify)** must be re-checked on the provider's website before you depend on it.

### Status board

| Phase | Name | Status | Date finished |
|---|---|---|---|
| 0 | Foundations and environment | ✅ |2026-10-26 |
| 1 | Repository, tooling, CI, Docker | ✅ |2026-10-28|
| 2 | Database and backend skeleton | ✅ |2026-10-28 |
| 3 | News collection | ✅ |2026-10-28 |
| 4 | Cleaning, dedup, embeddings, vector search | ✅ |2026-10-30 |
| 5 | Story grouping and timelines | ☐ | |
| 6 | Frontend MVP | ☐ | |
| 7 | LLM gateway and claim extraction | ☐ | |
| 8 | Evidence retrieval and verification | ☐ | |
| 9 | Bias, framing and source credibility | ☐ | |
| 10 | Grounded article writer and critic | ☐ | |
| 11 | Daily edition pipeline | ☐ | |
| 12 | Evaluation and LLMOps | ☐ | |
| 13 | MCP server | ☐ | |
| 14 | Production hardening | ☐ | |
| 15 | Deployment and launch | ☐ | |
| 16 | After launch | ☐ | |

---

## 1. The project in plain words

### 1.1 The problem
Today the same event is reported by many outlets. Each one chooses different words, leaves out different facts, and sometimes gets things wrong. A normal reader has to open five sites, compare them in their head, and still cannot tell what is solid and what is opinion.

### 1.2 The idea
**No Fake World** is a website that, once per day:

1. Collects news from many different sources around the world.
2. Groups articles that talk about the same event into one **story**.
3. Pulls out the **claims** ("the law passed 210–180") and checks each claim against evidence.
4. Compares **how** different outlets describe the same event (the framing).
5. Writes **one neutral, educational article** per story, where every sentence points to its sources.
6. Adds a **timeline** using older news, so the reader understands how we got here.

The reader can read the **daily edition**, **search** past editions, and **filter** by topic, country, date, language and reliability.

### 1.3 What the project is NOT
Be honest with users and with yourself:

- It does **not** find "the truth". It shows **what evidence supports**, **what evidence contradicts**, and **what is unclear**.
- It does **not** remove all bias. Choosing sources, models and thresholds is itself a choice. So we **show our method** and **show where sources disagree**.
- It does **not** copy articles. It writes its own summaries and links to the originals.
- It is **not real-time**. It publishes a **daily edition** (plus an optional midday update).

### 1.4 One example (end to end)
> Ten outlets report that "Country X passed a new energy law".
> The system groups them into one story, extracts claims such as "The vote was 210–180" and "The law bans new coal plants", finds that 8 sources agree on the vote count but only 2 mention the coal ban, and one outlet uses emotional wording ("shocking, reckless law").
> The article says: *"The law passed 210–180 (sources 1, 3, 5). Two sources report it bans new coal plants (sources 2, 4); this was not confirmed elsewhere. One outlet described the law as 'reckless' (source 7); this is an opinion, not a fact."* A timeline shows the earlier draft bill and the opposition's objections.

---

## 2. Design principles (the rules we never break)

1. **Every sentence has a citation.** No source, no sentence.
2. **Say "unclear" when unclear.** An honest "insufficient evidence" is a correct answer.
3. **Facts and framing are separate.** Verified claims go in one section. Opinions and wording differences go in another, labelled by outlet.
4. **Treat all fetched web text as untrusted.** Articles can contain hidden instructions (prompt injection). Never let article text trigger tools or change our prompts.
5. **Generate once, read many times.** Articles are built in a nightly batch and served from storage. Readers never trigger an AI call.
6. **Never depend on one provider.** Every external service (LLM, news API, database) sits behind our own interface so it can be swapped.
7. **Measure everything.** If we cannot score it, we cannot improve it.
8. **Be careful with wording.** Say "contradicted by [source]" or "no evidence found". Do not stamp "FAKE" on anyone.
9. **Respect copyright and robots.txt.** Store snippets and links, not full republished articles.
10. **Small steps, always working.** After each phase the project must run end to end, even if it is crude.

---

## 3. Glossary (simple words)

| Term | Simple meaning |
|---|---|
| **RSS** | A public list of a website's newest articles in a standard format. Free and easy to read by code |
| **GDELT** | A free, huge database of world news events and articles in many languages |
| **Ingestion** | Fetching articles and saving them in our database |
| **Extraction** | Taking the readable text out of a web page (removing ads and menus) |
| **Deduplication (dedup)** | Removing copies of the same article (for example, wire stories reprinted by many sites) |
| **Embedding** | A list of numbers that represents the meaning of a text. Similar meanings give similar numbers |
| **Vector database / pgvector** | A database that can search by meaning (closest numbers) instead of exact words |
| **Cosine similarity** | A score from −1 to 1 that tells how close two embeddings are |
| **Clustering** | Automatically grouping similar items. Here: grouping articles into stories |
| **Claim** | One checkable statement, e.g. "Unemployment fell to 4%" |
| **RAG (Retrieval-Augmented Generation)** | First *find* relevant evidence, then ask the AI to answer *using only that evidence* |
| **NLI (Natural Language Inference)** | A model that says whether text A *supports*, *contradicts* or is *neutral* to text B |
| **LLM** | A large language model, the AI that reads and writes text |
| **Hallucination** | The AI inventing facts that are not in the evidence |
| **Grounding / citation** | Forcing the AI's statements to be tied to a specific source |
| **Framing** | *How* a story is told (word choice, what is emphasised), not only *what* is said |
| **Bias** | A consistent lean in wording, selection or emphasis |
| **Prompt injection** | Hidden text in a web page that tries to give the AI new orders |
| **LLMOps** | The engineering around LLMs: routing, caching, tracing, testing, cost control |
| **Eval / golden set** | A hand-checked set of examples used to score our system |
| **MCP (Model Context Protocol)** | A standard way to expose tools and data so AI apps can use them |
| **Idempotent** | Safe to run twice. Running the same job again does not create duplicates |
| **Edition** | The set of articles published for one day |
| **UTC** | The world's reference time zone. We store all times in UTC |

---

## 4. Architecture

### 4.1 Big picture

```
                         ┌──────────────────────────── NIGHTLY BATCH ────────────────────────────┐
 ┌─────────────┐         │                                                                        │
 │ News sources│  hourly │  ┌────────┐  ┌────────┐  ┌──────────┐  ┌────────┐  ┌───────────────┐   │
 │ RSS · GDELT │────────▶│  │Collect │─▶│ Clean  │─▶│Embeddings│─▶│Cluster │─▶│Extract claims │   │
 │ Guardian/NYT│         │  │& store │  │& dedup │  │(vectors) │  │stories │  │   (LLM)       │   │
 │ Fact-checks │         │  └────────┘  └────────┘  └──────────┘  └────────┘  └──────┬────────┘   │
 └─────────────┘         │                                                           ▼            │
                         │  ┌───────────────┐  ┌──────────────┐  ┌───────────┐  ┌──────────────┐  │
                         │  │ Critic pass   │◀─│ Article      │◀─│Bias/framing│◀─│ Evidence +   │  │
                         │  │(delete unsup.)│  │ writer (LLM) │  │+ source    │  │ verification │  │
                         │  └──────┬────────┘  └──────────────┘  │ credibility│  │ (RAG + NLI)  │  │
                         │         ▼                              └───────────┘  └──────────────┘  │
                         │   Publish edition (DB rows + static JSON on CDN)                         │
                         └────────────────────────────────────────────────────────────────────────┘
                                                │
        ┌───────────────────────────────────────┴───────────────────────────────────────┐
        ▼                                                                               ▼
 ┌─────────────────┐   REST / JSON    ┌────────────────────┐   SQL + vectors   ┌───────────────┐
 │ React + TypeScript│◀──────────────▶│      FastAPI       │◀─────────────────▶│ Postgres +     │
 │ (reader website) │                  │ search · editions  │                   │ pgvector       │
 └─────────────────┘                  │ stories · sources  │                   └───────────────┘
                                      └─────────┬──────────┘
                                                │ same tools
                                      ┌─────────▼──────────┐
                                      │    MCP server      │  (tools for AI apps: search_news,
                                      └────────────────────┘   get_story, check_claim, ...)

 Cross-cutting: LiteLLM gateway · Redis cache · Langfuse tracing · Sentry · CI evals · Run log
```

### 4.2 The components, one by one

| Component | Job | Why it exists |
|---|---|---|
| **Collectors** | Fetch RSS, GDELT and API data on a schedule | Without data nothing else works |
| **Source registry** | A table describing each source: URL, country, language, licence, reliability notes | Lets us add/remove sources safely and show credibility |
| **Extractor** | Gets clean article text | Raw HTML is full of noise |
| **Dedup** | Detects copies | Otherwise one wire story counts as 20 "independent" sources |
| **Embedder** | Turns text into vectors | Enables search and grouping by meaning |
| **Clusterer** | Groups articles into stories | One story = one article for the reader |
| **Claim extractor (LLM)** | Lists checkable claims | We verify claims, not whole articles |
| **Retriever** | Finds evidence for each claim | RAG: the AI must use evidence, not memory |
| **Verifier (NLI + LLM judge)** | Labels claims supported / contradicted / unclear | The fact-checking core |
| **Bias/framing analyser** | Compares wording across outlets | Shows differences instead of hiding them |
| **Writer (LLM)** | Writes the cited article | The product the user reads |
| **Critic (LLM)** | Checks each sentence against its cited source and removes unsupported ones | Cuts hallucinations |
| **Edition publisher** | Freezes and publishes the day | Fast, cheap, reliable reading |
| **FastAPI** | Serves data to the website | Clean API for the frontend and MCP |
| **React + TS** | The website | What the user sees |
| **MCP server** | Exposes tools to AI apps | Extra portfolio value, and reuse |
| **LiteLLM gateway** | One interface to many LLM providers | Fallbacks, cost tracking, no lock-in |
| **Langfuse / logs** | Records every AI call | Debugging and quality control |
| **Scheduler** | Starts jobs at the right time | The "daily" part of the project |

### 4.3 A day in the life (times in IST; edition = 00:00–24:00 UTC, which is 05:30–05:30 IST)

| Time | Step | Plain meaning |
|---|---|---|
| Every hour | Collect | Fetch new articles, save them |
| 05:30 | Cut-off | The day is closed. Nothing new enters this edition |
| 05:30–06:30 | Clean, dedup, group | Remove copies, form stories |
| 06:30–07:30 | Claims, evidence, verification | Check what can be checked |
| 07:30–08:15 | Bias and framing | Compare how outlets tell the story |
| 08:15–09:00 | Write | One cited article per top story |
| 09:00–09:20 | Critic pass | Delete unsupported sentences |
| 09:30 | Publish | Edition goes live |
| 13:00 (optional) | Midday update | Refresh changed stories, add a visible "updated" note |

### 4.4 Rules for dates and timelines
1. Store **publication date** and **event date** separately.
2. Convert "yesterday", "last week" into real dates using the article's publication date (library: `dateparser`), and test it.
3. If a source only says "in October", store "October 2026" with *month* precision, never invent a day.
4. If sources disagree on a date, show both and their sources.
5. Link each new story to older stories by embedding similarity to build the timeline.
6. Every article shows **"Information as of <UTC time>"**.
7. Use `TIMESTAMPTZ` in Postgres and ISO-8601 in APIs.

---

## 5. Tech stack and why

| Layer | Choice | Why | Alternative |
|---|---|---|---|
| Main language | **Python 3.12** | Best ML/NLP ecosystem | — |
| Backend | **FastAPI**, Pydantic v2, SQLAlchemy 2, Alembic | Fast, typed, auto API docs | Django, Flask |
| Frontend | **React + TypeScript + Vite**, TanStack Query, Tailwind, shadcn/ui, Zod | Your chosen stack; typed and modern | Next.js |
| Database | **PostgreSQL + pgvector** | One database for tables and vectors; simple | Qdrant (dedicated vector DB) |
| Cache / queue | **Redis** (Upstash free tier or local) | Cache and job queue | Postgres-only queue to start |
| Jobs | **GitHub Actions cron** first, then ARQ/Celery, later Prefect | Free start, learn orchestration gradually | Dagster |
| Collection libs | `feedparser`, `httpx`, `trafilatura`, `dateparser` | Standard, reliable | `newspaper4k` |
| Embeddings | **multilingual-e5-small** (small, CPU) → later **bge-m3** (bigger) | Free, local, multilingual | Paid embedding APIs |
| Clustering | scikit-learn / HDBSCAN | Standard | BERTopic |
| Verification model | NLI model from Hugging Face (e.g. a DeBERTa-v3 NLI model, multilingual variant for non-English) **(verify exact model names)** | Free, local | LLM-only judge |
| LLM gateway | **LiteLLM** | One API for all providers, fallbacks, spend tracking | Direct SDKs |
| LLMs (cheap tier) | Gemini Flash / Flash-Lite free tier **(verify)** | Cheap, long context | Others |
| LLMs (fast/backup) | Groq-hosted open models (Llama, gpt-oss) **(verify)** | Fast, free tier | OpenRouter, Cloudflare Workers AI |
| Local dev LLM | **Ollama** | Free, no limits | — |
| Tracing / LLMOps | **Langfuse**, OpenTelemetry, promptfoo / DeepEval / RAGAS | Observability + evaluation | MLflow |
| Model lifecycle | MLflow or Weights & Biases, Hugging Face Hub, DVC | Track training and datasets | — |
| MCP | official Python MCP SDK | Expose tools to AI apps | — |
| Quality tools | pytest, ruff, mypy, pre-commit, Vitest, Playwright | Catch bugs early | — |
| Infra | Docker, docker-compose, GitHub Actions, Sentry, Grafana Cloud free | Production habits | — |
| Hosting | Frontend: Vercel or Cloudflare Pages. DB: Neon free tier or own VM. API/workers: a free VM or container host **(verify free limits)** | ≈ $0–5/month | — |

**Other languages to know:** **SQL** (essential), **Bash** and **YAML** (CI, Docker). **Go or Rust** only later and only if you need a very fast crawler. Do not start there.

**Estimated cost:** $0–5/month, plus an optional domain (~$10/year).

### 5.1 Free-tier reality check
- A free tier can **change, shrink or pause**. Keep fallbacks.
- Some free news APIs are **delayed (about 12 h)**, **truncated**, or **non-commercial / localhost only**. Do not build the core on them.
- Some free databases **pause after inactivity** or have a small size cap. Fine for development; check before launch.
- Free LLM tiers may use your prompts to improve their products. Send only **public news text**, never user secrets.
- Put every limit you rely on into `docs/limits.md` with the date you checked it.

---

## 6. Data sources

| Source | Use | Notes |
|---|---|---|
| **Publisher RSS** (BBC, Al Jazeera, DW, The Guardian, The Hindu, NDTV, and others across regions and viewpoints) | Core daily feed | Free, no quota. Store snippet + link |
| **GDELT** | Wide global coverage and history | Free, no key, 100+ languages. Noisy: filter by language and source whitelist |
| **Guardian Open Platform, NYT API** | Full text/archives for context | Free keys, read the terms |
| **Fact-check feeds** (Google Fact Check Tools API, ClaimReview markup, PolitiFact, BOOM, Alt News RSS) | Evidence for verification | Check quota and terms |
| **NewsData.io, GNews** | Only to fill gaps | No official Google News API exists; free tiers are limited |

**Pick sources across the political spectrum and across regions.** If all sources lean the same way, "multi-source" is an illusion. Record each source's lean (from public ratings such as AllSides, Ad Fontes, MBFC — as a *hint*, not truth) in the source registry.

---

## 7. Database design (first version)

All timestamps are `TIMESTAMPTZ` (UTC). Primary keys are UUIDs unless noted.

```sql
-- Sources we collect from
sources(
  id, name, homepage_url, feed_url, country, language,
  lean_hint TEXT,              -- e.g. left/center/right as a hint only
  reliability_hint NUMERIC,    -- 0..1, our own score, with notes
  license_notes TEXT, robots_ok BOOLEAN, is_active BOOLEAN,
  created_at
)

-- Raw articles as fetched
articles(
  id, source_id → sources, url UNIQUE, canonical_url,
  title, snippet, body_text,           -- body_text may be NULL if paywalled/not allowed
  language, published_at, fetched_at,
  content_hash TEXT,                   -- for exact dedup
  simhash BIGINT,                      -- for near-dup
  is_duplicate_of → articles NULL,
  status TEXT                          -- fetched | extracted | embedded | failed
)

-- Meaning vectors (store which model made them!)
article_embeddings(
  article_id → articles, model_name TEXT, dim INT,
  embedding vector(384),               -- size depends on model
  PRIMARY KEY (article_id, model_name)
)
-- Index: CREATE INDEX ON article_embeddings USING hnsw (embedding vector_cosine_ops);

-- Stories (clusters of articles about one event)
stories(
  id, first_seen_at, last_seen_at, title, summary_short,
  centroid vector(384), topic TEXT, country TEXT[],
  parent_story_id → stories NULL       -- link to earlier related story
)
story_articles(story_id, article_id, PRIMARY KEY(story_id, article_id))

-- Claims and verdicts
claims(
  id, story_id, article_id, text, claim_type TEXT,   -- fact | opinion | prediction
  event_date DATE, date_precision TEXT,              -- day | month | year
  created_at
)
evidence(
  id, claim_id, article_id NULL, fact_check_url NULL, passage TEXT,
  relation TEXT,                                     -- supports | contradicts | neutral
  nli_score NUMERIC, source_independent BOOLEAN
)
verdicts(
  id, claim_id, label TEXT,                          -- supported | contradicted | unclear
  confidence NUMERIC, explanation TEXT, model_version TEXT, created_at
)

-- Framing / bias observations
framing_notes(
  id, story_id, source_id, tone TEXT, loaded_terms TEXT[],
  emphasis TEXT, missing_points TEXT, model_version TEXT
)

-- The published product
editions(id, edition_date DATE UNIQUE, status TEXT,  -- building | published | delayed
         built_at, published_at)
articles_generated(
  id, edition_id, story_id, UNIQUE(edition_id, story_id),
  title, body_markdown, citations JSONB,
  critic_report JSONB, prompt_version TEXT, model_name TEXT,
  token_cost NUMERIC, version INT, updated_at, changelog JSONB
)

-- Operations
run_log(
  id, job_name, edition_date, started_at, finished_at, status,
  items_in INT, items_out INT, errors JSONB, token_cost NUMERIC
)
```

**Why these tables?** `articles` is raw input. `stories` are our unit of reading. `claims → evidence → verdicts` is the fact-checking chain. `articles_generated` is the product. `run_log` tells you what happened last night. `UNIQUE(edition_id, story_id)` makes re-running a day safe.

---

## 8. Repository layout

```
no-fake-world/
├─ README.md
├─ docs/
│  ├─ IMPLEMENTATION_PLAN.md      ← this file
│  ├─ decisions/                  ← one short file per big decision (ADR)
│  ├─ limits.md                   ← free-tier limits + date checked
│  └─ methodology.md              ← public explanation of how verdicts are made
├─ backend/
│  ├─ app/
│  │  ├─ api/                     ← FastAPI routes
│  │  ├─ core/                    ← settings, logging
│  │  ├─ db/                      ← models, session, migrations (alembic)
│  │  ├─ collectors/              ← rss.py, gdelt.py, factcheck.py
│  │  ├─ pipeline/                ← clean, dedup, embed, cluster, claims, verify, bias, write, critic
│  │  ├─ llm/                     ← gateway.py (LiteLLM), prompts/, schemas.py
│  │  └─ mcp_server/
│  ├─ tests/
│  ├─ pyproject.toml
│  └─ Dockerfile
├─ frontend/                      ← React + TypeScript (Vite)
├─ evals/                         ← golden sets, scoring scripts
├─ infra/                         ← docker-compose.yml, deployment notes
└─ .github/workflows/             ← ci.yml, nightly.yml
```

---

# PHASES

> Time estimates assume 8–12 hours per week. If you have less, stretch the calendar, never the quality checks.

---

## Phase 0 — Foundations and environment
**Time:** Week 1 (26 Oct – 1 Nov)

**Goal:** A working computer setup and a basic understanding of the tools.

**Why:** Most early problems are setup problems. Fix them once.

**Learn first**
- Git basics: commit, branch, pull request.
- Python virtual environments and `pip`/`uv`.
- What an HTTP API is (GET/POST, JSON, status codes).
- What a database table, primary key, and index are.
- Docker idea: a box that holds your app and its dependencies.

**Steps**
1. Install: Git, Python 3.12, Node.js (LTS), Docker Desktop, VS Code, and a GitHub account with SSH or token login.
2. Create a GitHub repository `no-fake-world` (private at first is fine).
3. Install Postgres through Docker (you will do this properly in Phase 2). For now confirm `docker run hello-world` works.
4. Create accounts (free): Gemini API (Google AI Studio), Groq, Langfuse (cloud free tier), Sentry, Neon (optional), Vercel. Store keys in a password manager, **never in Git**.
5. Create `docs/limits.md` and write down each service's free limits and today's date **(verify on each site)**.
6. Copy this plan into `docs/IMPLEMENTATION_PLAN.md`.

**Done when**
- [ ] `python --version`, `node --version`, `docker --version`, `git --version` all work.
- [ ] Repo exists on GitHub with this plan committed.
- [ ] API keys exist and are saved somewhere safe, not in the repo.
- [ ] `docs/limits.md` filled in.

**If you get stuck:** Docker on Windows needs WSL2 enabled. Search the exact error message; most setup errors have a one-line fix.

---

## Phase 1 — Repository, tooling, CI, Docker
**Time:** Week 1–2

**Goal:** An empty but professional project skeleton where tests and checks run automatically.

**Why:** Good habits at the start cost almost nothing. Fixing a messy repo later costs weeks.

**Learn first:** `pytest`, linting (what `ruff` does), type checking (what `mypy` does), what CI is, `.env` files and why secrets stay out of Git.

**Steps**
1. Create the folder layout from Section 8 (empty folders with `.gitkeep`).
2. Backend: create `pyproject.toml` (use `uv` or `poetry`), add `fastapi`, `uvicorn`, `pydantic-settings`, `sqlalchemy`, `alembic`, `psycopg`, `httpx`, `pytest`, `ruff`, `mypy`.
3. Add a `/health` endpoint:
   ```python
   from fastapi import FastAPI
   app = FastAPI(title="No Fake World API")

   @app.get("/health")
   def health():
       return {"status": "ok"}
   ```
4. Write one test that calls `/health` and checks `status == "ok"`.
5. Add `pre-commit` with ruff and mypy so bad code cannot be committed.
6. Create `.env.example` (names only, no values) and add `.env` to `.gitignore`.
7. Write `backend/Dockerfile` and `infra/docker-compose.yml` with two services: `api` and `db` (image with pgvector, e.g. `pgvector/pgvector:pg16`).
8. Create GitHub Actions `ci.yml`: install, ruff, mypy, pytest. It must run on every pull request.
9. Frontend: `npm create vite@latest frontend -- --template react-ts`; add ESLint and Vitest; make one passing test.
10. Protect the `main` branch: changes only through pull requests with passing CI.

**Done when**
- [ ] `docker compose up` starts API and database.
- [ ] `http://localhost:8000/health` returns ok and `/docs` shows the API page.
- [ ] CI is green on GitHub.
- [ ] Frontend dev server runs.

**If you get stuck:** If the API cannot reach the database inside Docker, use the service name (`db`) as the host, not `localhost`.

---

## Phase 2 — Database and backend skeleton
**Time:** Week 2

**Goal:** All core tables exist and the API can read and write them.

**Why:** Everything else stores data here. A clean schema prevents painful rewrites.

**Learn first:** SQL (`SELECT`, `JOIN`, `GROUP BY`, indexes, unique constraints, `TIMESTAMPTZ`), SQLAlchemy models, Alembic migrations, what pgvector adds.

**Steps**
1. Enable the extension in a first migration: `CREATE EXTENSION IF NOT EXISTS vector;`
2. Create SQLAlchemy models for the tables in Section 7 (start with `sources`, `articles`, `run_log`; add the rest as you reach their phases).
3. Generate and run migrations with Alembic. **Never** edit tables by hand; always write a migration.
4. Add a database session helper and settings loaded from environment variables.
5. Add endpoints: `GET /sources`, `POST /sources` (admin only later), `GET /articles?limit=`.
6. Write tests with a throw-away test database.
7. Write a short SQL practice file (`docs/sql_practice.md`): five queries you wrote by hand (e.g., "articles per source per day").

**Done when**
- [ ] `alembic upgrade head` creates tables from scratch on an empty database.
- [ ] You can insert a source and read it through the API.
- [ ] Tests pass in CI with a database.

**If you get stuck:** If Alembic does not detect a model change, check that the model module is imported in `env.py`.

---

## Phase 3 — News collection
**Time:** Week 3 (9–15 Nov)

**Goal:** Fresh articles from at least **20 sources** appear in the database automatically.

**Why:** No data, no product.

**Learn first:** RSS/Atom format, HTTP caching headers (`ETag`, `If-Modified-Since`), `robots.txt`, rate limiting and politeness, Python `async` with `httpx`, how `trafilatura` extracts text.

**Steps**
1. Fill the **source registry**: choose 20–30 sources across regions and viewpoints. For each: feed URL, language, country, licence notes, `robots_ok`.
2. Write `collectors/rss.py`:
   - fetch each feed with a timeout and a polite User-Agent,
   - skip feeds not modified since last time,
   - save new items (`title`, `url`, `snippet`, `published_at`) with `status = fetched`.
3. Make inserts **idempotent**: `url` is `UNIQUE`; use `INSERT ... ON CONFLICT DO NOTHING`.
4. Write `collectors/gdelt.py`: fetch recent articles, **filter** by language and your source whitelist. Start small.
5. Write the **extractor**: for allowed sources fetch the page, run `trafilatura`, store `body_text`. If extraction fails or the page is paywalled, keep the snippet and set `status = failed` with a reason.
6. Add `run_log` entries for each run: counts and errors.
7. Add a CLI command: `python -m app.collectors.run --once`.
8. Schedule it **hourly** with a GitHub Actions cron workflow (`nightly.yml` will later be extended) or a local cron while developing.
9. Write tests with saved sample feeds (no live network in tests).

**Done when**
- [ ] Running the collector twice does not create duplicates.
- [ ] After 24 hours you have a few hundred articles from many sources.
- [ ] Failures are logged, not silent.
- [ ] You can answer: "How many articles per source yesterday?" with a SQL query.

**If you get stuck:** Some sites block bots. Do not bypass blocks or ignore `robots.txt`; drop the source or use only its RSS snippet.

---

## Phase 4 — Cleaning, dedup, embeddings, vector search
**Time:** Week 4

**Goal:** Remove copies and make articles searchable **by meaning**.

**Why:** Wire stories are reprinted everywhere. Counting them as independent sources would fake agreement.

**Learn first:** hashing, SimHash/MinHash (near-duplicate detection), what an embedding is, cosine similarity, HNSW index, `sentence-transformers`, why we store the embedding model name.

**Steps**
1. **Clean:** strip HTML leftovers, normalise whitespace, detect language, canonicalise URLs (remove tracking parameters).
2. **Exact dedup:** compute `content_hash` of cleaned text; mark identical ones.
3. **Near dedup:** compute a SimHash or MinHash; mark articles whose similarity is above a threshold as `is_duplicate_of` the earliest one. Keep a small test list of known duplicate pairs and check it.
4. **Embed:** run `multilingual-e5-small` (384 dimensions) on `title + first 300 words`. Process in batches on CPU. Save `model_name` and `dim`.
5. Create the HNSW index on the embedding column.
6. Add an endpoint `GET /search?q=` that embeds the query and returns the nearest articles.
7. Add **hybrid search**: combine keyword search (Postgres full-text) and vector search, e.g. with reciprocal rank fusion. Compare results by hand on 10 queries.
8. Record timing: how long does embedding 1,000 articles take on your machine?

**Done when**
- [ ] Duplicate rate is visible (e.g., "12% of yesterday's articles were duplicates").
- [ ] Searching "inflation in Europe" returns relevant results even if the exact words differ.
- [ ] Changing the embedding model would not corrupt data (you stored `model_name`).

**If you get stuck:** If embeddings are slow, shorten the text, use batches, or run embedding in a nightly job only.

---

## Phase 5 — Story grouping and timelines
**Time:** Week 5

**Goal:** Turn articles into **stories** and connect each story to older ones.

**Why:** Readers want one article per event, and context from the past.

**Learn first:** clustering (HDBSCAN vs. threshold-based grouping), centroids, precision vs. recall in grouping, time windows.

**Steps**
1. For one edition day, take all non-duplicate articles with embeddings.
2. **Group:** begin with the simplest approach: for each article find the nearest existing story centroid within the last 72 hours; if cosine similarity ≥ a threshold (start around 0.80, tune it), attach; else start a new story. Update the centroid.
3. Try HDBSCAN as an experiment and compare with the threshold method on a hand-labelled sample of 50 articles.
4. Give each story a working title (the most central article's title for now).
5. **Link to the past:** for each story search older stories (previous 90 days) by centroid similarity; set `parent_story_id` if similarity is high and the topic matches.
6. Build a **timeline** query: all linked stories ordered by date, with `event_date` and `date_precision`.
7. Implement date parsing rules from Section 4.4 and unit-test at least 10 tricky phrases ("yesterday", "last Friday", "in October", "Q3").
8. Rank stories by importance for the edition: number of **independent** sources × source diversity × recency. Start with the top 10.

**Done when**
- [ ] On your 50-article test sample, you can state the grouping precision and recall (even roughly).
- [ ] A story page query returns its articles and a timeline.
- [ ] Date-parsing tests pass, including midnight/time-zone edge cases.

**If you get stuck:** If unrelated stories merge, raise the threshold or add a rule requiring shared named entities (people/places).

---

## Phase 6 — Frontend MVP
**Time:** Week 6

**Goal:** A real website that shows editions, stories, search and filters, using the data you already have.

**Why:** A visible product keeps motivation high and shows problems in the API early.

**Learn first:** React components and hooks, TypeScript types, TanStack Query (fetching/caching), React Router, Tailwind, accessibility basics (labels, contrast, keyboard use), Zod for validating API data.

**Steps**
1. Generate TypeScript types from the FastAPI OpenAPI schema (tool: `openapi-typescript`), so frontend and backend never disagree.
2. Pages: **Home** (today's edition), **Story/Article page**, **Search results**, **Source page**, **About/Methodology**.
3. Components: story card, filter bar (topic, country, language, date range, reliability), citation list, timeline, "Information as of" label, loading/error/empty states.
4. Article page layout: summary → **Verified facts** → **Where sources differ** → **Timeline** → **Sources** (with credibility badges) → corrections log.
5. Use fake/sample article JSON at first so the UI can be built before Phase 10.
6. Add keyboard navigation, alt text, proper headings, light/dark mode.
7. Write a few Vitest tests and one Playwright test: open home → open a story → see sources.
8. Deploy a preview to Vercel on every pull request.

**Done when**
- [ ] The site works on phone and desktop.
- [ ] Filters change the results via the API.
- [ ] Lighthouse accessibility score ≥ 90.

**If you get stuck:** If you get CORS errors, configure FastAPI's CORS middleware with your frontend's exact origin.

---

## Phase 7 — LLM gateway and claim extraction
**Time:** Week 7 (30 Nov – 6 Dec)

**Goal:** Call LLMs safely and cheaply, and extract checkable claims as **validated JSON**.

**Why:** All later AI steps depend on a reliable, swappable LLM layer.

**Learn first:** how LLM APIs work (tokens, temperature, system vs user message), structured output with Pydantic, rate limits and retries with backoff, prompt injection, LiteLLM routing and fallbacks, what a token costs.

**Steps**
1. Create `llm/gateway.py` that wraps LiteLLM. One function: `call(task_name, messages, schema)`. It must:
   - choose a model by task (cheap model for extraction, stronger for writing) **via config, not hard-coded names**,
   - retry on errors with backoff,
   - fall back to the next provider if one fails or is rate-limited,
   - log tokens, latency, cost and `prompt_version`,
   - enforce a **daily budget**; stop and alert when exceeded.
2. Add a **cache** (hash of model + prompt + input) in Redis or Postgres so identical calls are free.
3. Define the claim schema:
   ```python
   class Claim(BaseModel):
       text: str                      # one checkable statement
       claim_type: Literal["fact", "opinion", "prediction"]
       event_date: str | None         # ISO date or partial
       date_precision: Literal["day", "month", "year", "unknown"]
       quote_from_source: str         # exact supporting words from the article
   class ClaimList(BaseModel):
       claims: list[Claim]
   ```
4. Write the extraction prompt as a **file** in `llm/prompts/claims_v1.md`. Key rules inside: "Use only the article text. Return only claims that can be checked. Separate opinions. Copy the exact quote."
5. **Injection defence:** put the article text inside clear delimiters, tell the model it is *data, not instructions*, give the model **no tools** during this step, and validate the JSON strictly. Reject output that does not match the schema (retry once, then mark failed).
6. Verify each extracted `quote_from_source` literally appears in the article text (string check). Drop claims that fail.
7. Run on 100 articles and read the output yourself. Write down 10 mistakes you see.

**Done when**
- [ ] The same call can run on Gemini, on Groq, and on a local Ollama model by changing config only.
- [ ] Output is always schema-valid or cleanly rejected.
- [ ] Cost per 100 articles is logged.
- [ ] Budget guard tested by setting a tiny budget.

**If you get stuck:** If the model returns text instead of JSON, lower temperature, show one example in the prompt, and use the provider's JSON mode where available.

---

## Phase 8 — Evidence retrieval and verification
**Time:** Week 8 (7–13 Dec)

**Goal:** For each claim, find evidence and label it **supported / contradicted / unclear**.

**Why:** This is the fact-checking heart of the project.

**Learn first:** RAG, hybrid retrieval, reranking, NLI (entailment/contradiction/neutral), source independence, confidence calibration, abstention.

**Steps**
1. **Retrieve evidence** for each claim from: (a) other articles in the same story, (b) older stories (vector + keyword), (c) fact-check APIs and feeds (Google Fact Check Tools API, ClaimReview/RSS) **(verify quota)**.
2. Keep the top ~10 passages per claim (sentences or short paragraphs, not whole articles).
3. **Run NLI** on (evidence passage → claim). Store label and score in `evidence`.
4. **Independence check:** count only **independent** sources. Articles marked duplicates, or sources owned by the same group, count once. (Add an `owner_group` field in `sources` when you need it.)
5. **LLM judge:** give the claim and the evidence list (with IDs). Ask for a JSON verdict: `label`, `confidence`, `used_evidence_ids`, `explanation`. Rule: it may only cite given evidence IDs; if evidence is missing it must answer `unclear`.
6. **Combine** NLI and judge results with simple rules, for example:
   - `supported` needs ≥ 2 independent supporting sources and no strong contradiction,
   - `contradicted` needs a strong contradicting source or a fact-check,
   - otherwise `unclear`.
7. Save in `verdicts` with `model_version`.
8. Hand-label **100 claims** (this is your first golden set, see Phase 12) and compare.

**Done when**
- [ ] Every claim ends with a verdict and at least one evidence link, or `unclear`.
- [ ] You can report accuracy on your 100 hand-labelled claims (even if low, write it down).
- [ ] Verdict explanations never cite evidence that was not retrieved.

**If you get stuck:** If almost everything becomes `unclear`, your retrieval is too narrow. Widen the time window, add more sources, or lower the support threshold, and measure the effect.

---

## Phase 9 — Bias, framing and source credibility
**Time:** Week 9–10 (14–27 Dec)

**Goal:** Show **how** outlets differ, and give each source an honest reliability profile.

**Why:** A user trusts the system more when it shows differences instead of claiming to be perfectly neutral.

**Learn first:** types of media bias (word choice, selection/omission, emphasis, framing), inter-annotator agreement, fine-tuning a small transformer, evaluation metrics (precision, recall, F1, macro-F1), dataset licences, limits of LLM judges (they have their own leaning).

**Steps**
1. **Framing comparison per story:** for each source in a story, ask the LLM (schema-validated) for: tone, loaded words (copy exact words), what it emphasises, what other sources mention that it does not. Show these in "Where sources differ".
2. **Sentence-level bias classifier (training project):**
   - get a bias-annotated sentence dataset such as **BABE** (search the Hugging Face hub for the current dataset page) **(verify licence)**,
   - fine-tune a small model (DistilBERT/RoBERTa; XLM-R for multilingual),
   - track runs in MLflow or W&B,
   - report macro-F1 on a held-out set.
3. **Compare** the classifier with an LLM judge on 100 sentences you label yourself. Note where they disagree.
4. **Source credibility profile** (transparent formula, shown on the source page): correction history, agreement with other independent sources, ratio of claims later contradicted, plus public ratings as a *hint*. Show components, not just one number.
5. **Calibration:** check that "confidence 0.8" is right about 80% of the time on your labelled set; adjust.
6. Never show a political label as truth. Show "rated by X as …" with the source of the rating.

**Done when**
- [ ] Each story shows a "Where sources differ" block with real examples.
- [ ] Classifier results and limits are written in `docs/methodology.md`.
- [ ] Each source page lists how its credibility score was computed.

**If you get stuck:** Small datasets overfit. Use a train/validation/test split from the start and keep the test set untouched until the end.

---

## Phase 10 — Grounded article writer and critic
**Time:** Week 11 (28 Dec – 3 Jan)

**Goal:** Generate one **neutral, educational, fully cited** article per story.

**Why:** This is the product readers see.

**Learn first:** prompt structure, grounded generation, citation formats, summarisation faithfulness, "LLM-as-judge" critic patterns, reading-level control.

**Steps**
1. **Prepare the writer's input** (and nothing else): the story's verified claims with verdicts and evidence IDs, framing notes, the timeline, and short source snippets. The writer sees **no web access and no memory**.
2. **Article structure** (fixed template):
   1. Headline (neutral wording)
   2. In 3 sentences (plain words)
   3. What is confirmed (verified facts with citations)
   4. What is disputed or unclear
   5. How different outlets describe it
   6. Timeline: how we got here
   7. Key terms explained (glossary for the story)
   8. Sources
3. **Writer prompt rules:** every sentence ends with citation IDs; use only provided material; avoid loaded words; plain language (target a school-grade reading level); say "unclear" when marked unclear; never mention things not in the input.
4. **Critic step:** split the article into sentences. For each sentence + its cited passages ask: "Does the source support this sentence? yes/partly/no". Delete or rewrite `no` and `partly`. Save the critic report in `critic_report`.
5. **Mechanical checks:** every sentence has ≥ 1 citation; every cited ID exists; no quote longer than a few words from a source (copyright); dates match the timeline.
6. Save `body_markdown`, `citations`, `prompt_version`, `model_name`, cost.
7. Generate 20 articles and read them yourself. Score each 1–5 on: accurate, neutral, clear, useful. Write the weak spots into a list for the next prompt version.

**Done when**
- [ ] 100% of sentences in published articles have valid citations.
- [ ] The critic removes at least some unsupported sentences in tests (proves it works), and removal counts are logged.
- [ ] Your own review score averages ≥ 4 on "accurate".

**If you get stuck:** If articles are dull or too long, tighten the template and set per-section length limits. Do not loosen the citation rule.

---

## Phase 11 — Daily edition pipeline
**Time:** Week 12 (4–10 Jan)

**Goal:** One command (and one schedule) builds and publishes a whole day, safely, every day.

**Why:** Automation is what makes it a product, not a demo.

**Learn first:** job orchestration, idempotency, retries, backfills, run logs, alerting, UTC day boundaries.

**Steps**
1. Create `pipeline/build_edition.py` with ordered steps from Section 4.3. Each step reads its input from the database and writes its output to the database, so any step can be re-run alone.
2. Use the key `(edition_date, story_id)` for generated content so re-runs update instead of duplicating.
3. **Edition states:** `building → published` or `delayed`. The website only shows `published`.
4. **Failure handling:**
   - retry transient failures,
   - if a story fails, skip it and continue,
   - if the whole run fails, keep yesterday's edition visible with a "delayed" notice and **alert yourself** (email/Telegram/Discord webhook).
5. **Budget guard:** stop LLM calls when the daily budget is hit; publish what is ready.
6. **Backfill command:** `python -m app.pipeline.build_edition --date 2026-11-02` to rebuild any past day. Use it to fill your archive.
7. **Publish:** store the final edition as rows in the DB **and** as a static JSON snapshot (served by a CDN), so readers still see content if the API is down.
8. **Scheduling:** start with GitHub Actions `schedule:` cron. Remember cron runs in UTC. Later, move to a worker + queue if needed.
9. Add the **midday update** job (optional) with a visible "updated at" and a changelog entry.
10. Write an **incident note** template in `docs/runbook.md`: "what to do if the nightly job fails".

**Done when**
- [ ] A full edition builds automatically 7 days in a row.
- [ ] Re-running a date produces no duplicates.
- [ ] You get an alert when you deliberately break the job.
- [ ] `run_log` shows time, counts, and cost for each run.

**If you get stuck:** GitHub Actions jobs have time limits and can be delayed. If your pipeline is too heavy, run it on your own VM or split into smaller jobs.

---

## Phase 12 — Evaluation and LLMOps
**Time:** Week 13 (11–17 Jan) — but start small evals from Phase 7 onward

**Goal:** Measure quality and block changes that make it worse.

**Why:** Without measurement you cannot tell if a new prompt or model is better or worse.

**Learn first:** golden datasets, precision/recall/F1, faithfulness and citation precision, LLM-as-judge limits, regression testing, tracing, prompt versioning, A/B comparison.

**Steps**
1. **Build the golden sets** (store in `evals/`, version with DVC or Git LFS):
   - 200–500 claims with human verdicts,
   - 50 stories with a short human checklist ("must mention X", "must not claim Y"),
   - 100 sentences with bias labels,
   - 50 article pairs for duplicate detection,
   - 30 prompt-injection attack texts.
2. **Metrics:**
   - claim extraction: precision/recall against labelled claims,
   - verification: accuracy and macro-F1, **abstain rate**, calibration,
   - article: **citation precision** (does the source support the sentence), **faithfulness** (share of sentences supported), neutrality score (human), readability,
   - safety: injection success rate (target 0),
   - ops: p95 latency, cost per article, failure rate, fallback rate.
3. Tools: **promptfoo** or **DeepEval** for LLM tests, **RAGAS** for retrieval/faithfulness style metrics, plain `pytest` for the rest.
4. **CI gate:** a GitHub Action runs the small eval set on every pull request that touches prompts, models or pipeline code. It **fails** if a key metric drops by more than an agreed margin.
5. **Tracing:** connect **Langfuse** so every LLM call shows prompt, response, cost, latency, and link to the story. Add OpenTelemetry traces across the pipeline.
6. **Prompt registry:** prompts live in Git with versions (`claims_v1`, `claims_v2`). Every output stores its `prompt_version`.
7. **Model comparison:** run the same golden set across two models; record results in a table in `docs/evals.md`.
8. **Human feedback loop:** the website has a "report an error" button → writes to a review queue → you label → the example joins the golden set.
9. **Dashboards:** Grafana (or a simple page) with daily cost, daily article count, verdict distribution, abstain rate, fallback rate.

**Done when**
- [ ] One command prints all metrics: `python -m evals.run_all`.
- [ ] CI blocks a deliberately bad prompt change.
- [ ] Langfuse shows traces for a full edition run.
- [ ] `docs/evals.md` contains real numbers and the date.

**If you get stuck:** If your golden set feels too small, that is normal. Start with 50 and grow it every time you find a real error.

---

## Phase 13 — MCP server
**Time:** Week 13–14

**Goal:** Expose your data and checks as **MCP tools** so AI apps can use them.

**Why:** It is a modern interface, reuses your work, and is strong portfolio value.

**Learn first:** what MCP is (tools, resources, prompts), JSON-RPC basics, tool schemas, authentication, why MCP tools must be **read-only and rate-limited**.

**Steps**
1. Use the official Python MCP SDK.
2. Implement read-only tools:
   - `search_news(query, from_date?, to_date?, country?)`
   - `get_story(story_id)` → article + verified claims + timeline
   - `get_timeline(story_id)`
   - `check_claim(text)` → retrieves evidence and returns a verdict **with citations** (rate-limited; uses the cache)
   - `get_source_profile(source_id)`
3. Add input validation and size limits on every tool.
4. Add authentication (API key) and per-key rate limits.
5. Test with an MCP client (for example Claude Desktop or the MCP inspector) and write a short demo in the README.
6. **Security:** never let tool output include raw untrusted HTML; treat tool inputs as untrusted; no write tools.

**Done when**
- [ ] An MCP client can call all five tools and gets cited answers.
- [ ] Unauthorised calls are rejected.
- [ ] Tool calls appear in your logs.

---

## Phase 14 — Production hardening
**Time:** Week 14 (18–24 Jan)

**Goal:** Make it safe, observable, recoverable.

**Learn first:** OWASP Top 10, secrets management, rate limiting, backups and restores, structured logging, health checks, SLO/SLI basics.

**Steps**
1. **Security:** HTTPS only; secure headers; CORS limited to your domain; input validation (Pydantic); rate limiting (e.g., `slowapi`); dependency scanning (Dependabot, `pip-audit`, `npm audit`); secret scanning; least-privilege database user.
2. **Auth:** public pages need none. Admin routes (sources, review queue) need login (JWT or a managed auth provider).
3. **Privacy:** collect minimal user data; no tracking beyond privacy-friendly analytics; write a simple privacy page.
4. **Observability:** structured JSON logs, request IDs, Sentry for errors, Grafana dashboards, an uptime check (free uptime monitor) on `/health` and the home page.
5. **Backups:** daily database backup to storage; **test a restore** at least once and write the steps in `docs/runbook.md`.
6. **Performance:** add indexes found by `EXPLAIN ANALYZE`; paginate everything; cache read endpoints; run a small load test (e.g., k6 or Locust) and note p95.
7. **Resilience:** timeouts and retries on all outbound calls; circuit-breaker idea for failing providers; the static JSON edition fallback tested by turning the API off.
8. **Legal and ethics pages:** `Methodology`, `Corrections policy`, `Copyright and takedown`, `Known limitations`.

**Done when**
- [ ] Security scans show no high-severity open issues.
- [ ] You restored a backup into an empty database successfully.
- [ ] The site still shows today's edition when the API is stopped.
- [ ] Load test results are written down.

---

## Phase 15 — Deployment and launch
**Time:** Week 15 (25–31 Jan 2027)

**Goal:** A public, stable website.

**Steps**
1. Choose hosting **(verify free limits first)**: frontend on Vercel/Cloudflare Pages; database on a provider that does not sleep, or on your own VM; API and workers on a free VM or container host.
2. Build production Docker images in CI and deploy from `main` after tests pass (CD).
3. Set production environment variables and secrets in the host's secret manager.
4. Point a domain (optional), enable HTTPS.
5. Run the pipeline in production for **7 days quietly**; fix problems.
6. Soft launch to friends; gather feedback through the error-report button.
7. Write the **launch post / README / demo video**: problem, architecture diagram, real eval numbers, what you learned, known limits.
8. Add a **status page** and a **changelog**.

**Done when**
- [ ] Public URL works and the edition updates daily without you.
- [ ] Alerts reach you.
- [ ] README includes architecture, setup, eval results, limits.

---

## Phase 16 — After launch (continuous)

Weekly routine (30–60 minutes):
- Read `run_log` and the dashboard: cost, failures, abstain rate.
- Review the error-report queue; add real errors to the golden set.
- Check provider limits and prices in `docs/limits.md`; update dates.
- Review 5 random published articles by hand.

Ideas for later (only after the core is stable): more languages (Hindi, Malayalam, Tamil), email digest, topic subscriptions, claim-check browser extension, reading-level toggle, source-ownership graph, cross-language story linking.

---

## 17. Calendar summary (targets)

| Dates | Phases |
|---|---|
| 26 Oct – 1 Nov | 0, start 1 |
| 2 – 8 Nov | 1, 2 |
| 9 – 15 Nov | 3 |
| 16 – 22 Nov | 4 |
| 23 – 29 Nov | 5 |
| 30 Nov – 6 Dec | 6, 7 |
| 7 – 13 Dec | 8 |
| 14 – 27 Dec | 9 |
| 28 Dec – 3 Jan | 10 |
| 4 – 10 Jan | 11 |
| 11 – 17 Jan | 12, 13 |
| 18 – 24 Jan | 14 |
| 25 – 31 Jan 2027 | 15 |

If you fall behind, **cut features, not tests**: first drop MCP (Phase 13), then the bias classifier fine-tune (keep LLM framing notes), then the midday update. Never drop: citations, critic pass, evals, backups.

---

## 18. Resume protocol (if you stopped for days or weeks)

1. Open the **Status board** (top of this file). Find the first unfinished phase.
2. Read that phase's **Goal**, **Why**, and **Done when**.
3. Run the project: `docker compose up`, open `/health` and the website. Fix anything broken first.
4. Run tests and evals: `pytest`, then `python -m evals.run_all` (once it exists). Note the numbers.
5. Read the last 5 files in `docs/decisions/` and the last week of `run_log`.
6. Re-check `docs/limits.md`: free tiers may have changed **(verify)**.
7. Write today's date and one sentence "where I am" at the bottom of the **Work log** below.
8. Continue from the first unticked step. Do not redo finished phases.


### Work log (append one line per session)

| Date | Phase | What I did | What is next |
|---|---|---|---|
| 2026-10-24 | 0 | Wrote the full plan and architecture. Installed Git, Node 22, Docker and VS Code; Python 3.13 was installed, so I pinned Python 3.12 with `uv`. Created the private GitHub repo `no-fake-world` and committed the plan, `.env.example` and `docs/limits.md`. Rule: keys never go into Git. | Mark Phase 0 done; FastAPI skeleton |
| 2026-10-24 to 2026-10-25 | 1A | FastAPI skeleton with `/health`, pytest, ruff, mypy. Removed an unwanted `src/` layout (`package = false`). Added Ruff settings so the import order is the same from any folder. | Pre-commit hooks |
| 2026-10-25 to 2026-10-28 | 1B | Pre-commit hooks (ruff, ruff format, mypy), proved by a blocked commit (my first test passed only because the file was unsaved). Docker Compose with Postgres + pgvector 0.8.7; port 5432 was used by an older Postgres, so the host port is 5433 (a swapped `5432:5433` line caused one failed start). Dockerfile for the API (uv, non-root user). CI with backend and Docker jobs. | Learn the pull request flow; frontend |
| 2026-10-28 | 1C | Practised branch, pull request, squash merge. Proved CI catches mistakes (a deliberate wrong test turned CI red, then green). Merged the CI PR (#1). React + TypeScript + Vite skeleton with ESLint and Vitest; fixed an npm ERESOLVE conflict by pinning TypeScript to 6.0 instead of `--force`; added the frontend CI job (#2). | Mark Phase 1 done; database connection |
| 2026-10-28 | 1 done, 2A | Phase 1 marked done (#3). Settings, SQLAlchemy engine and `/health/db`; the API container reaches the database at `db:5432`, my machine at `127.0.0.1:5433` (#4). | Alembic migrations |
| 2026-10-28 | 2B | Alembic with `sources`, `articles`, `run_log`; fixed a `CREATE EXTENSION vector` line that sat outside `upgrade()`; tested the migration on an empty scratch database (#5). Sources API with tests against a real Postgres, also in CI; tightened URL validation after Swagger's placeholder `https://` was accepted (#6). Phase 2 done. | Collect real news |
| 2026-10-28 | 3A | Seeded 8 feeds (BBC, Al Jazeera, DW, The Guardian, NPR, France 24, Sky News, The Hindu) and a feed checker; all 8 worked (about 330 entries). Pre-commit's mypy ran from the repo root and missed the config; fixed with `--config-file` (#7). | RSS collector |
| 2026-10-28 | 3B | RSS collector: idempotent (unique URL + `ON CONFLICT DO NOTHING`), URL cleaning, one failing feed cannot stop the others, every run logged in `run_log`, tests with a fake internet. Second real run: 320 entries seen, 2 new (#8). | Article text |
| 2026-10-28 | 3C | robots.txt-aware text extraction (trafilatura), only for sources I enable after reading their terms. Enabled The Guardian: 10 of 10, then 20 of 20 extracted, clean text. Wrote `docs/data-handling.md` (#9). | Close Phase 3 |
| 2026-10-28 | 3 done | `collect.ps1`, data notes, Phase 3 marked done (#10). The scheduled task was not actually registered (found missing on 2026-10-30). | Embeddings |
| 2026-10-28 | 4A | pgvector table with HNSW index; multilingual-e5-small in an optional `ml` dependency group (keeps CI and Docker small); vector search CLI. 328 articles embedded (model download 167 s, embedding 10.3 s). The script stopped on a harmless Hugging Face warning; fixed with exit-code checks and `HF_HUB_OFFLINE` (#11). | Duplicates, hybrid search |
| 2026-10-29 | 4B1 | Duplicate detection: cosine >= 0.95 AND 3-word shingle Jaccard >= 0.3. Labelled 53 pairs. First mistake: I labelled same-event pairs as copies; fixed after reading the texts (1 true copy). 1 copy marked among 333 articles (#12). | Hybrid search |
| 2026-10-29 | 4B2 | Hybrid search: generated tsvector column with GIN index, reciprocal rank fusion, "no good match" rule. Compared keyword, vector and hybrid on 10 real and 10 off-topic queries; threshold 0.83 (off-topic max 0.813, real min 0.844). Found that the keyword side over-matches long Guardian bodies (a474e26). | Close Phase 4 |
| 2026-10-30 | 4 done | Rewrote the search notes, added off-topic queries, set threshold 0.83, marked Phase 4 done (9364b9f). | Group articles into stories |
| 2026-10-30 | maintenance | Found the scheduled task did not exist and nothing had been collected since 28 Oct. Caught up by hand (224 articles embedded, 557 total). | Story labels |
| 2026-10-30 to 2026-11-03 | 5A | Story-pair labelling. First pass wrong: I answered "same writing?" instead of "same development?" (3 same out of 49). Re-judged: 32 same, 48 different. Cosine alone peaks at F1 0.81 (0.86 to 0.87); the overlap band is a fuzzy boundary between storyline and development. Decision: group storylines with a 72-hour window (b808008). Task registered (state Ready) by 3 Nov. | Story tables and grouping |
| 2026-11-04 | 5B | `stories` and `story_articles`; average-linkage grouping (scipy) with a 72-hour window; evaluate on 1,145 articles (precision 0.88, recall 0.70 at 0.85); group_run: 503 stories, largest 54, 342 singletons. Alembic timed out once because Docker was stopped. Found: group_run deletes all stories each run, story titles borrow one outlet's headline, outlet counts are not independence (5c436bb). | Reliability checks |
| 2026-11-07 | quality | Collector ran in only 12 of 73 hours; the `FAILED` lines were Docker Desktop not running. Added container restart policy, a database step in `collect.ps1`, task wake settings. Dedup on the larger data: 18 flagged (17 same-outlet re-listings, 1 cross-outlet); the tuner's recall of 0.72 exposed 7 pairs I had mislabelled; notes updated (16c9b06). | Dedup time gate |
| 2026-11-08 | 4B1 fix | Dedup v2: near copies must also be close in time (same outlet within 30 minutes, other outlets within 6 hours), so a results page is no longer hidden behind a live blog. 33 tests. Restored a deleted plan line; `collect.ps1` now skips cleanly when Docker is down. | Merge it; Phase 5C-1: stable story ids |
| 2026-11-09 | 5C-1 | Stable story ids: stories older than 96 hours are frozen, only recent articles are regrouped, and a new group keeps the id of the old story it contains at least half of. Bootstrapped 14 days (863 stories); two more runs gave created=0 removed=0 and the top ids did not change. Copies are kept inside stories. Story counts per day dip when the laptop was off. `rebuild_run` added to the hourly script. | 5C-2: independent outlets, publication rule, ranking |
| 2026-11-09 | 5C-2 | Added independent_outlet_count (outlets that reprint each other count once), original_count, a publication rule of 3 independent outlets and a top_stories ranking with a preview command. A failing test exposed that the test database did not empty `stories`, so a frozen story leaked into the next test. | 5D: timelines and developments inside big stories |
| 2026-11-09 | dedup audit | Audited 19 new pairs: the labelling export ignored the time gate, two identical pairs were mislabelled, and same-outlet updates with changed figures (Yemen 33 vs 22, Krakow 6 vs 5) were being hidden. Dedup v3: figures-conflict gate, one shared rule function (`is_near_copy`), an evaluation tool. Backfilled 6 stories left at independent_outlet_count 0 by the migration default. | Close dedup |
| 2026-11-10 | dedup close | Found that "copy" has two meanings (hide-safe for the same outlet, shared origin for other outlets), which made the first evaluation (precision 0.68, recall 0.83) misleading. The label tool now prints the matching rule per pair and evaluation is split by outlet type. Reviewed the 13 mistake pairs and changed 6 labels. Result: same outlet precision 0.84, recall 0.88 (tp 21, fp 4, fn 3, tn 21); other outlet 3 of 47 marked, all 3 real reprints. `mark_run` marks 35 near copies; a 60-day rebuild (2,688 articles, 1,218 stories) changed nothing and the stale-story check returned 0. 41 tests pass. | 5D: story chains |



### Decision log (keep each entry short)

| Date | Decision | Reason | Alternatives rejected |
|---|---|---|---|
| 2026-10-24 | React + TypeScript + FastAPI | Chosen stack, matches goals | Next.js, Django |
| 2026-10-24 | Daily batch edition, not real-time | Cheaper, more accurate, fits free tiers | Real-time generation |
| 2026-10-24 | Postgres + pgvector first | One database, simple | Dedicated vector DB (later if needed) |

---

## 19. Troubleshooting cheat sheet

| Symptom | Likely cause | First thing to try |
|---|---|---|
| API cannot reach DB in Docker | Using `localhost` | Use service name `db` |
| Alembic misses changes | Models not imported | Import models in `env.py` |
| Many duplicate articles | Thresholds too loose, URLs not canonicalised | Strip tracking params, tune SimHash threshold |
| Wrong stories merged | Similarity threshold too low | Raise threshold; require shared named entities |
| LLM returns invalid JSON | Prompt too loose | Lower temperature, add example, validate and retry once |
| 429 rate-limit errors | Free tier limits | Back off, spread calls over the night, use fallback provider |
| Costs jump suddenly | Retry loop or huge inputs | Check Langfuse; cap tokens per call; budget guard |
| Almost all verdicts "unclear" | Weak retrieval | Widen window, add sources, inspect retrieved passages |
| Articles contain unsupported sentences | Writer ignoring rules | Stronger critic, shorter input, stricter template |
| Dates off by one day | Time zone confusion | Store UTC; test midnight cases |
| Nightly job did not run | Cron in UTC, workflow disabled after inactivity | Check Actions tab; re-enable; add heartbeat alert |
| Site blank for readers | API down | Serve static edition JSON from CDN |

---

## 20. Environment variables (names only; values go in `.env`, never in Git)

```
DATABASE_URL=
REDIS_URL=
GEMINI_API_KEY=
GROQ_API_KEY=
OPENROUTER_API_KEY=
LANGFUSE_PUBLIC_KEY=
LANGFUSE_SECRET_KEY=
LANGFUSE_HOST=
SENTRY_DSN=
GUARDIAN_API_KEY=
NYT_API_KEY=
GOOGLE_FACTCHECK_API_KEY=
DAILY_LLM_BUDGET_USD=
ALERT_WEBHOOK_URL=
ADMIN_JWT_SECRET=
MODEL_CHEAP=         # e.g. a Gemini Flash family model (verify current name)
MODEL_FAST_FALLBACK= # e.g. a Groq-hosted open model (verify current name)
MODEL_WRITER=
EMBEDDING_MODEL=
```

---

## 21. What to study, in order (with the key terms)

1. **Web and Python basics:** HTTP, REST, JSON, async/await, type hints, virtual environments.
2. **SQL and Postgres:** joins, indexes, `EXPLAIN`, transactions, constraints, migrations.
3. **Data collection:** RSS/Atom, robots.txt, rate limiting, ETags, extraction, idempotent ingestion.
4. **NLP and retrieval:** tokenisation, embeddings, cosine similarity, BM25, hybrid search, reranking, clustering.
5. **LLM engineering:** tokens, temperature, structured output, prompt versioning, grounding, hallucination, prompt injection.
6. **Verification:** claims, check-worthiness, NLI (entailment/contradiction/neutral), stance, source independence, calibration, abstention. Study the FEVER and CheckThat! tasks.
7. **Media bias:** word-choice, selection, omission, framing, source-level vs article-level bias, inter-annotator agreement.
8. **ML basics for fine-tuning:** train/validation/test split, overfitting, precision/recall/F1, macro-F1, experiment tracking.
9. **LLMOps:** gateway, fallbacks, caching, tracing, evals, regression gates, cost control.
10. **Frontend:** React, TypeScript, TanStack Query, Tailwind, accessibility, testing.
11. **DevOps and security:** Docker, CI/CD, secrets, OWASP, backups, observability, SLOs.
12. **Responsible AI and law:** copyright basics, defamation risk, transparency, corrections policy.

Suggested reading (search these titles): FastAPI official docs; the pgvector README; Hugging Face NLP/LLM course; SQLAlchemy 2 tutorial; React and TypeScript docs; "Designing Data-Intensive Applications" (selected chapters); the LiteLLM, Langfuse, promptfoo and MCP documentation; research papers on media bias (BABE) and fact verification (FEVER).

---

## 22. Final checklist before you call it "production-grade"

- [ ] Automated daily edition for 14 days without manual fixes
- [ ] Every published sentence has a valid citation; critic pass logged
- [ ] Real evaluation numbers published on the methodology page
- [ ] CI blocks quality regressions
- [ ] Alerts, dashboards, run log, status page
- [ ] Backups tested by restoring
- [ ] Security scan clean; secrets out of Git
- [ ] Static fallback works when API is down
- [ ] Methodology, corrections, copyright and limitations pages live
- [ ] README with architecture diagram, setup steps, results, and honest limits

*End of plan. Next action: start Phase 0, Step 1.*
