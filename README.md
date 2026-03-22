# Armenian Bank Voice Agent — Aram (Արամ)

An end-to-end Voice AI customer support agent for Armenian banks, built with the open-source **LiveKit framework** and **OpenAI** models. The agent speaks and understands Armenian and answers questions about loans, deposits, and branch locations for Amio Bank, Ameria Bank, and Fast Bank.

---

## Table of Contents


1. [Architecture & Design Decisions](#architecture--design-decisions)
2. [Project Structure](#project-structure)
3. [Setup Instructions](#setup-instructions)
4. [How to Run](#how-to-run)
5. [How to Use](#how-to-use)

---

## Architecture & Design Decisions

### High-Level Pipeline

Every time the user speaks, the following pipeline runs:

```
User Voice
    │
    ▼
VAD (Silero)              ← detects when user starts/stops speaking
    │
    ▼
STT (OpenAI Whisper-1)    ← transcribes Armenian speech → text
    │
    ▼
LLM (GPT-4o-mini)         ← generates response using bank data + memory
    │
    ▼
Confidence Check          ← appends disclaimer if response is uncertain
    │
    ▼
TTS (GPT-4o-mini-tts)     ← converts response text → Armenian speech
    │
    ▼
Agent Voice
```

### Component Breakdown

| Component | Technology | Why |
|-----------|-----------|-----|
| **Voice framework** | LiveKit (open-source) | Required by project spec; handles real-time WebRTC audio, room management, and agent worker lifecycle — runs fully locally without cloud dependency |
| **VAD** | Silero | Lightweight, accurate, runs locally — detects speech start/end without sending audio to an API |
| **STT** | OpenAI Whisper-1 | Best-in-class Armenian language recognition; `language="hy"` parameter ensures Armenian-first transcription |
| **LLM** | GPT-4o-mini | Fast, cost-efficient, and accurate enough for FAQ-style banking questions; `temperature=0.3` keeps answers stable and factual |
| **TTS** | GPT-4o-mini-tts (voice: onyx) | Produces natural-sounding Armenian speech; `onyx` voice has a calm, professional tone suitable for a banking assistant |
| **Memory** | Custom `ConversationMemory` | Keeps the last 10 messages in context so the agent remembers what was said earlier in the conversation |

### Key Design Decisions

**1. Local LiveKit server (not cloud)**
The agent runs entirely on a local LiveKit server (`livekit-server --dev`). This avoids cloud dependency, keeps data local, and follows the open-source requirement of the project.

**2. Bank data via web scraping**
Bank information (loans, deposits, branches) is scraped from the real websites of Amio, Ameria, and Fast Bank using `scraper.py` and saved as JSON files. This data is injected directly into the LLM system prompt so the agent always answers based on real bank data rather than hallucinating.

**3. Confidence checking**
`utils/confidence.py` scans every LLM response for uncertainty keywords (`կարծում եմ`, `հավանաբար`, `probably`, etc.). If found, it appends a disclaimer telling the user to verify the information directly with the bank. This is critical for financial data.

**4. Self-loop prevention**
An `is_agent_speaking` flag prevents the agent from picking up its own TTS output as user input — a common problem in voice agents without proper acoustic echo cancellation.

**5. Graceful shutdown & inactivity timeout**
`utils/shutdown.py` runs a background monitor that ends the session if the user leaves the room or is inactive for 10 minutes, preventing orphaned agent processes.

**6. Session metrics tracking**
`utils/metrics.py` tracks STT, LLM, and TTS latency for every turn and logs a full session summary when the agent shuts down.

**7. Language detection module (built, not yet wired)**
`utils/language.py` is built and capable of detecting Armenian, Russian, and English input by measuring the ratio of Armenian Unicode characters. It is ready to be wired into the session to block non-Armenian input in a future update.

**8. Error handling module (built, not yet wired)**
`utils/errors.py` is built with `tenacity` retry logic (3 attempts, exponential backoff) and Armenian-language error messages. It is ready to be connected to the session error handler in a future update.

---

## Project Structure

```
armenian_bank_agent/
├── agent.py              # Main entry point — LiveKit worker + AgentSession pipeline
├── scraper.py            # Scrapes bank websites → saves JSON to bank_data/
├── data_loader.py        # Loads bank JSON and formats it for the LLM system prompt
├── bank_data/            # Auto-generated folder with scraped bank data
│   ├── amio.json
│   ├── ameria.json
│   └── fast.json
├── utils/
│   ├── __init__.py
│   ├── memory.py         # Stores last 10 conversation messages for LLM context
│   ├── confidence.py     # Detects uncertain responses and appends disclaimer ✅ active
│   ├── language.py       # Detects Armenian / Russian / English 🔧 built, not yet wired
│   ├── metrics.py        # Tracks STT / LLM / TTS latency per turn and session ✅ active
│   ├── shutdown.py       # Graceful shutdown + 10-minute inactivity timeout ✅ active
│   └── errors.py         # Retry logic + Armenian error messages 🔧 built, not yet wired
├── .env                  # API keys — never commit to GitHub
├── .gitignore
├── requirements.txt
└── README.md
```

---

## Setup Instructions

### Prerequisites

- Python 3.10+
- `livekit-server` binary ([download here](https://github.com/livekit/livekit/releases))
- `lk` CLI binary ([download here](https://github.com/livekit/livekit-cli/releases))
- An OpenAI API key ([get one here](https://platform.openai.com/api-keys))

### 1. Clone the repo

```bash
git clone https://github.com/your-username/armenian_bank_agent.git
cd armenian_bank_agent
```

### 2. Create and activate virtual environment

```bash
python -m venv venv

# Windows
.\venv\Scripts\Activate.ps1

# Mac / Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

Or manually:

```bash
pip install livekit-agents livekit-plugins-openai livekit-plugins-silero
pip install requests beautifulsoup4 python-dotenv tenacity
```

### 4. Configure .env

Create a `.env` file in the project root:

```env
LIVEKIT_URL=ws://localhost:7880
LIVEKIT_API_KEY=devkey
LIVEKIT_API_SECRET=secret
OPENAI_API_KEY=sk-...your_key_here...
```

### 5. Scrape bank data

Run this once to generate the `bank_data/` folder:

```bash
python scraper.py
```

This creates `amio.json`, `ameria.json`, and `fast.json` with loans, deposits, and branch data scraped from each bank's website.

---

## How to Run

Start each of the following in a **separate terminal**, in this order:

### Terminal 1 — Start LiveKit server

```bash
# Windows
.\livekit-server.exe --dev

# Mac / Linux
livekit-server --dev
```

Wait until you see `starting LiveKit server`.

### Terminal 2 — Start the agent

```bash
python agent.py dev
```

Wait until you see:
```
registered worker {"agent_name": "armenian-bank-agent", "url": "ws://localhost:7880"}
```

### Terminal 3 — Generate a join token

```bash
# Windows
.\lk.exe token create --api-key devkey --api-secret secret --join --room test-room --identity user1

# Mac / Linux
./lk token create --api-key devkey --api-secret secret --join --room test-room --identity user1
```

Copy the token from the output.

### Browser — Join the room

1. Go to [https://agents-playground.livekit.io](https://agents-playground.livekit.io)
2. Click **Manual**
3. Enter:
   - **URL:** `ws://localhost:7880`
   - **Token:** *(paste token from Terminal 3)*
4. Click **Connect** and allow microphone access

### Terminal 4 — Dispatch the agent

```bash
# Windows
.\lk.exe dispatch create --url ws://localhost:7880 --api-key devkey --api-secret secret --room test-room --agent-name armenian-bank-agent

# Mac / Linux
./lk dispatch create --url ws://localhost:7880 --api-key devkey --api-secret secret --room test-room --agent-name armenian-bank-agent
```

---

## How to Use

Once connected, the agent greets you in Armenian:

> *"Բարև։ Ես Արամն եմ։ Ձեր բանկային օгнаканը։ Ինчо՞в карող ем огнел։"*

You can ask questions in Armenian about:

| Topic | Armenian | Example question |
|-------|----------|-----------------|
| Loans | Վарկер | «Амио банки варкери токосадрույцнере канի՞ токос ен։» |
| Deposits | Аванднер | «Америа банкум аванди токоснере ի՞нч ен։» |
| Branches | Маснаճыуղер | «Фасть банкի маснаճыуղерը орте՞ղ ен гтнвум։» |

The agent will politely decline any question outside these three topics.
