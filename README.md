# Armenian Bank Voice AI Support Agent

> An end-to-end Voice AI customer support agent for Armenian banks, built using the **open-source LiveKit Agents framework**. The agent understands and speaks Armenian, answering questions exclusively about Credits, Deposits, and Branch Locations using data scraped directly from official Armenian bank websites.

---

## Table of Contents

- [Overview](#overview)
- [Architecture & Design Decisions](#architecture--design-decisions)
- [Tech Stack & Model Choices](#tech-stack--model-choices)
- [Data Strategy](#data-strategy)
- [Project Structure](#project-structure)
- [Setup Instructions](#setup-instructions)
- [Running the Agent](#running-the-agent)
- [Testing](#testing)
- [Scalability](#scalability)

---

## Overview

**Agent name:** Արամ (Aram)  
**Language:** Armenian (հայերեն)  
**Scope:** Credits, Deposits, Branch Locations only  
**Banks covered:** Amio Bank, Ameriabank, Fast Bank  
**Framework:** LiveKit Agents (open-source)

---

## Architecture & Design Decisions

The system follows a real-time voice pipeline:

```
User Speech
    │
    ▼
VAD (Silero) ── detects speech boundaries
    │
    ▼
STT (Whisper-1) ── transcribes Armenian speech to text
    │
    ▼
LLM (GPT-4o-mini) ── generates Armenian response using bank data from system prompt
    │
    ▼
TTS (OpenAI TTS-1) ── converts text to natural speech
    │
    ▼
Audio Response to User
```

### Component Breakdown

**`agent.py`** — Main entrypoint. Initializes the AgentSession with STT/LLM/TTS/VAD, injects bank data into the system prompt, handles session lifecycle.

**`data_loader.py`** — Loads all bank JSON files and concatenates them into a single string passed directly to the LLM system prompt on every request.

**`scraper.py`** — Scrapes official bank websites using BeautifulSoup and saves data as JSON files per bank.

**`utils/confidence.py`** — Detects if the LLM response contains uncertainty keywords and appends a disclaimer prompting the user to verify with the bank directly.

**`utils/language.py`** — Detects if the user spoke a non-Armenian language using character-set analysis, so the agent can respond appropriately.

**`utils/memory.py`** — Maintains a rolling conversation history (last 10 turns) using LiveKit's ChatContext API.

**`utils/metrics.py`** — Tracks per-turn and session-level latency metrics (STT, LLM, TTS durations).

**`utils/shutdown.py`** — Handles graceful session shutdown with farewell messages. Monitors participant presence and enforces a 10-minute inactivity timeout.

**`utils/errors.py`** — Handles API errors (rate limits, timeouts, connection failures) with exponential backoff retry logic using `tenacity`.

---

## Tech Stack & Model Choices

| Component | Choice | Reason |
|-----------|--------|--------|
| **Framework** | LiveKit Agents (open-source) | Required by assignment; provides real-time audio pipeline, room management, VAD integration |
| **STT** | OpenAI `whisper-1` | Best-in-class Armenian language support. Correctly transcribes Armenian even when mixed with Russian or English words. Reliable and cost-effective. |
| **LLM** | OpenAI `gpt-4o-mini` (temp 0.3) | Fast response times critical for voice UX. Low temperature reduces hallucination and keeps answers grounded in bank data. Cost-effective for high query volumes. |
| **TTS** | OpenAI `tts-1`, voice `alloy` | Natural-sounding synthesis. The `alloy` voice provides a professional, neutral tone appropriate for banking. `tts-1` is optimized for low latency. |
| **VAD** | Silero VAD | Official recommendation for LiveKit Agents. Lightweight, runs on CPU without GPU. Accurately detects Armenian speech boundaries. |

### Dependencies & Versions

> Run `pip show <package>` in your virtual environment to get exact installed versions.

```
livekit-agents          # pip show livekit-agents
livekit-plugins-openai  # pip show livekit-plugins-openai
livekit-plugins-silero  # pip show livekit-plugins-silero
python-dotenv           # pip show python-dotenv
tenacity                # pip show tenacity
requests                # pip show requests
beautifulsoup4          # pip show beautifulsoup4
torch                   # pip show torch
openai                  # pip show openai
```

**Python:** 3.12.10  
**Platform tested:** Windows 11

---

## Data Strategy

No vector database or embeddings are used. All bank data is loaded as a single concatenated string and injected directly into the LLM system prompt on every request.

**Why this approach:**
- Maximum context availability — the LLM always has complete bank data
- Simple to update — re-run `scraper.py` to refresh data, no re-indexing required
- Easy to evaluate and debug — the exact data sent to the LLM is always visible
- Consistent behavior — no retrieval variability between calls

**Data format injected into system prompt:**
```
=== Amio Bank ===

[ՎԱՐԿԵՐ]
<scraped loans page text>

[ԱՎԱՆԴՆԵՐ]
<scraped deposits page text>

[ՄԱՍՆԱՃՅՈՒՂԵՐ]
<scraped branches page text>
```

---

## Project Structure

```
armenian_bank_agent/
├── agent.py                 # Main agent entrypoint
├── data_loader.py           # Loads bank JSON data → system prompt string
├── scraper.py               # Scrapes official bank websites → JSON files
├── .env                     # Environment variables (not committed to repo)
├── bank_data/               # Scraped bank data
│   ├── amio.json
│   ├── ameria.json
│   └── fast.json
└── utils/
    ├── __init__.py
    ├── confidence.py        # Uncertainty detection & disclaimer injection
    ├── errors.py            # API error handling with retry logic
    ├── language.py          # Armenian language detection
    ├── memory.py            # Conversation history (rolling 10-turn window)
    ├── metrics.py           # STT/LLM/TTS latency tracking
    └── shutdown.py          # Graceful shutdown & inactivity monitoring
```

---

## Setup Instructions

### Prerequisites

- Python 3.11 or higher
- OpenAI API key — [platform.openai.com](https://platform.openai.com)
- LiveKit Cloud account (free tier) — [cloud.livekit.io](https://cloud.livekit.io)
- LiveKit CLI binary (`lk` / `lk.exe`) — [github.com/livekit/livekit-cli/releases](https://github.com/livekit/livekit-cli/releases)

### Step 1 — Clone the repository

```bash
git clone <repository-url>
cd armenian_bank_agent
```

### Step 2 — Create virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### Step 3 — Install dependencies

```bash
pip install livekit-agents livekit-plugins-openai livekit-plugins-silero \
            python-dotenv tenacity requests beautifulsoup4 torch
```

### Step 4 — Configure environment variables

Create a `.env` file in the project root:

```env
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=your_livekit_api_key
LIVEKIT_API_SECRET=your_livekit_api_secret
OPENAI_API_KEY=your_openai_api_key
```

LiveKit credentials: [cloud.livekit.io](https://cloud.livekit.io) → your project → Settings → Keys.

### Step 5 — Scrape bank data

```bash
python scraper.py
```

This creates `bank_data/amio.json`, `bank_data/ameria.json`, `bank_data/fast.json` with loans, deposits, and branch data scraped from official bank websites.

---

## Running the Agent

```bash
python agent.py dev
```

The agent connects to LiveKit Cloud and registers as a worker named `armenian-bank-agent`.

Expected output:
```
INFO  livekit.agents  starting worker
INFO  livekit.agents  registered worker {"agent_name": "armenian-bank-agent", "url": "wss://..."}
```

---

## Testing

### Option A — LiveKit Agents Playground

1. Open [agents-playground.livekit.io](https://agents-playground.livekit.io)
2. Sign in with your LiveKit Cloud account
3. Select your project and connect to room `test-room`
4. The agent joins automatically and greets you in Armenian

### Option B — LiveKit CLI dispatch

In a separate terminal while the agent is running:

```bash
lk dispatch create \
  --url wss://your-project.livekit.cloud \
  --api-key YOUR_API_KEY \
  --api-secret YOUR_API_SECRET \
  --room test-room \
  --agent-name armenian-bank-agent
```

### Sample queries

```
Amio բանկի վարկերի տոկոսադրույքները որքան են?
Ameriabank-ի մասնաճյուղերը որտե՞ղ են:
Fast Bank-ում ավանդ կարո՞ղ եմ բացել:
Ի՞նչ կարող ես ինձ ասել Fast Bank-ի ավանդների մասին:
```

The agent will **refuse** questions outside its scope:
```
— Ո՞ր ռեստորաններն են մոտ բանկին:
✓ Կներեք, ես կարող եմ օգնել միայն վարկերի, ավանդների և մասնաճյուղերի վերաբերյալ հարցերով։
```

---

## Scalability

Adding a new bank requires only two changes:

**1. `data_loader.py`** — add the bank to `BANK_NAMES`:
```python
BANK_NAMES = {
    "amio":    "Amio Bank",
    "ameria":  "Ameriabank",
    "fast":    "Fast Bank",
    "newbank": "New Bank Name",   # ← add here
}
```

**2. `scraper.py`** — add the bank's URLs to `BANKS`:
```python
"newbank": {
    "loans":    "https://www.newbank.am/loans",
    "deposits": "https://www.newbank.am/deposits",
    "branches": "https://www.newbank.am/branches"
}
```

Then re-run `python scraper.py` — no other changes needed.
