# LinkedIn AI Poster — LangGraph Agent

An autonomous daily agent that fetches AI news, writes a short LinkedIn post, reviews it, then sends it to you on Telegram before publishing to LinkedIn.

---

## Overview

This project is a LangGraph-powered pipeline that runs once a day. It searches the web for the latest AI news across multiple angles, ranks the most newsworthy article, writes a short punchy post in your voice, reviews it for accuracy and quality, and then — after sending you a preview on Telegram — publishes it to LinkedIn.

---

## Architecture

```
Daily Scheduler (GitHub Actions cron)
        │
        ├──────────────────────────────────────────┐
        │                                          │
   [parallel asyncio]                              │
        │                                          │
   ┌────┴─────┐  ┌──────────┐  ┌──────────┐  ┌───┴──────┐
   │AI releases│  │AI policy │  │AI research│  │AI business│
   │fetch node │  │fetch node│  │fetch node │  │fetch node │
   └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘
        │              │              │              │
        └──────────────┴──────────────┴──────────────┘
                               │
                               ▼
                      rank_articles node
                               │
                               ▼
                        write_post node
                               │
                               ▼
                      review_agent node
                      ┌────────┴────────┐
                   FAIL                PASS
                      │                 │
                      │         notify_telegram node  ← ① you see it first
                      │                 │
                      │          post_linkedin node   ← ② goes public
                      │                 │
                 (rewrite, max          END
                   3 retries)
```

---

## Nodes

### 1. Daily Scheduler
Triggers the entire pipeline once per day at 08:00 UTC via the GitHub Actions workflow in `.github/workflows/daily-dispatch.yml`. Running `python main.py` locally (no flags) uses APScheduler instead; `python main.py --once` runs a single pass.

### 2. Fetch Nodes (×4, parallel)
Four independent search nodes run concurrently via `asyncio`. Each targets a different angle of AI news using the **Ollama Web Search API** (`ollama.com/api/web_search`):

| Node | Search Query |
|---|---|
| AI releases | `"new AI model 2026"` |
| AI policy | `"AI regulation news today"` |
| AI research | `"AI research paper today"` |
| AI business | `"AI industry funding 2026"` |

Each node returns a list of articles with `title`, `url`, and `snippet`. All results are merged into the shared LangGraph state.

### 3. `rank_articles` Node
Gemini scores all fetched articles across all 4 search lanes. It selects the single most newsworthy, relevant, and recent article. The winner — `{title, url, summary}` — is written to state.

### 4. `write_post` Node
Gemini writes one short LinkedIn post from the ranked article. The post format is fixed:

```
[Audience hook]: [Source] reports [key insight]. [One-line takeaway].

Link: [article url]
```

Example:
```
For AI builders and security teams: Reuters reports that Bessent and Powell
warned major bank CEOs about AI model risks. AI security is now a board-level
issue, not just a research topic.

Link: https://reuters.com/...
```

The post is stored in state as `draft_post`.

### 5. `review_agent` Node
A Gemini reviewer sees both the original article and the draft post side by side. It checks:

- **Accuracy** — does the post faithfully reflect the article? No hallucinated claims.
- **Tone** — appropriate for a professional LinkedIn audience.
- **Format** — correct structure (hook + insight + Link).
- **Quality** — clear, concise, no filler.

**Decision:**
- `PASS` → continue to `notify_telegram`
- `FAIL` → write feedback into state, loop back to `write_post` for a rewrite

The retry counter is tracked in state. After **3 failed attempts**, the pipeline exits gracefully rather than looping indefinitely.

### 6. `notify_telegram` Node *(runs first)*
Sends the approved post to you via the **Telegram Bot API** (`sendMessage`). This is intentionally the first publish step — you see exactly what is going out before it hits LinkedIn publicly.

### 7. `post_linkedin` Node *(runs second)*
Publishes the post to LinkedIn via the **LinkedIn REST API** (`/v2/ugcPosts`). Requires a registered LinkedIn Developer app with `w_member_social` OAuth scope.

---

## LangGraph Shared State

All nodes read from and write to a single `TypedDict` state object:

```python
class PosterState(TypedDict):
    # Search
    news_results: list[dict]          # all articles from all 4 lanes

    # Ranking
    ranked_article: dict              # {title, url, summary}

    # Writing
    draft_post: str                   # current draft
    review_feedback: str              # reviewer's notes on last draft
    retry_count: int                  # number of rewrite attempts

    # Publishing
    telegram_status: str              # "sent" | "failed"
    linkedin_status: str              # "posted" | "failed"
```

---

## Tech Stack

| Component | Tool |
|---|---|
| Agent framework | LangGraph |
| LLM | Google Gemini (`google-genai`, structured output) |
| Web search | Ollama Web Search API |
| Scheduler | GitHub Actions cron (APScheduler for local runs) |
| LinkedIn | LinkedIn REST API v2 |
| Telegram | Telegram Bot API |
| Language | Python 3.11+ |
| Async | `asyncio` for parallel search nodes |

---

## Environment Variables

```env
# Gemini
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-flash-lite-latest

# Ollama (web search only)
OLLAMA_API_KEY=your_ollama_api_key

# LinkedIn (set POST_LINKEDIN=true to publish)
POST_LINKEDIN=false
LINKEDIN_ACCESS_TOKEN=your_linkedin_oauth_token
LINKEDIN_AUTHOR_URN=urn:li:person:YOUR_ID

# Telegram
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_personal_chat_id
```

---

## Deployment (GitHub Actions)

The workflow `.github/workflows/daily-dispatch.yml` runs the pipeline daily at 08:00 UTC and can also be triggered manually from the **Actions** tab (`workflow_dispatch`). After each run it commits `last_article.json` back to the repo so the ranker remembers recently posted articles.

In **Settings → Secrets and variables → Actions**, add:

| Type | Name |
|---|---|
| Secret | `GEMINI_API_KEY`, `OLLAMA_API_KEY`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `LINKEDIN_ACCESS_TOKEN`, `LINKEDIN_AUTHOR_URN` |
| Variable (optional) | `GEMINI_MODEL` (default `gemini-flash-lite-latest`), `POST_LINKEDIN` (default `false`) |

GitHub cron runs can start a few minutes late, and scheduled workflows are disabled after 60 days of no repository activity (the daily history commit keeps it active).

---

## Project Structure

```
linkedin-ai-poster/
├── README.md
├── .env
├── main.py                  # entry point (--once for a single run)
├── .github/workflows/       # daily GitHub Actions cron
├── llm_client/gemini.py     # Gemini structured-output helper
├── graph.py                 # LangGraph graph definition + edges
├── state.py                 # PosterState TypedDict
├── nodes/
│   ├── fetch_news.py        # 4 parallel search nodes
│   ├── rank_articles.py     # article ranking node
│   ├── write_post.py        # post writing node
│   ├── review_agent.py      # review + conditional edge logic
│   ├── notify_telegram.py   # Telegram publish node
│   └── post_linkedin.py     # LinkedIn publish node
├── prompts/
│   ├── rank.txt             # ranking prompt template
│   ├── write.txt            # writing prompt template
│   └── review.txt           # review guidelines prompt
└── requirements.txt
```

---

## Flow Summary

1. GitHub Actions fires at 08:00 UTC
2. 4 search nodes run in parallel → ~8–16 articles collected
3. Ranker picks the single best article
4. Writer produces a short post (2–4 sentences + link)
5. Reviewer approves or sends back for rewrite (max 3 attempts)
6. On approval: Telegram notification sent to you first
7. Then: post published to LinkedIn
8. Pipeline ends
