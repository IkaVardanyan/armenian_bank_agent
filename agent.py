# ================================================================
# ENVIRONMENT + LOGGING SETUP
# ================================================================

import os
from dotenv import load_dotenv

# Load your secrets from .env (not pushed to GitHub)
load_dotenv()  

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET")
LIVEKIT_URL = os.getenv("LIVEKIT_URL")

# ================================================================
# IMPORTS
# ================================================================

import asyncio                # For async operations (real-time voice handling)
import logging                # For printing logs (debugging, monitoring)
from dotenv import load_dotenv  # Loads environment variables from .env

# LiveKit core classes
from livekit.agents import (
    AutoSubscribe,   # Controls what we subscribe to (audio/video)
    JobContext,      # Context of current session (room, participants)
    WorkerOptions,   # Config for running the agent
    cli,             # CLI runner for the agent
    AgentSession,    # Main pipeline (STT → LLM → TTS)
    Agent,           # The AI brain (instructions + behavior)
)

# Plugins for AI
from livekit.plugins import openai, silero

# Your custom modules
from data_loader import load_bank_data
from utils.memory import ConversationMemory
from utils.confidence import check_confidence
from utils.metrics import TurnMetrics, SessionMetrics
from utils.shutdown import monitor_participant


# ================================================================
# ENVIRONMENT + LOGGING SETUP
# ================================================================

load_dotenv()  # Load API keys (like OpenAI key) from .env file

# Configure logging format
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

# Create logger for this app
logger = logging.getLogger("armenian-bank-agent")


# ================================================================
# LOAD BANK DATA + SYSTEM PROMPT
# ================================================================

# Load your dataset (loans, deposits, branches)
BANK_DATA = load_bank_data()

# This is the "brain instruction" for the AI
SYSTEM_PROMPT = f"""
Դուք հայկական բանկերի վիրտուալ ձայնային օգնական եք։
Ձեր անունը «Արամ» է։

Դուք ՄԻՇՏ խոսում եք հայերեն։

Թույլատրված թեմաներ՝
1. Վարկեր
2. Ավանդներ
3. Մասնաճյուղեր

Եթե հարցը դուրս է թեմայից՝
«Կներեք, ես կարող եմ օգնել միայն վարկերի, ավանդների և մասնաճյուղերի վերաբերյալ հարցերով։»

Պատասխանները կարճ և հստակ։
Օգտագործեք {BANK_DATA}
"""


# ================================================================
# MAIN FUNCTION (ENTRYPOINT)
# ================================================================

async def entrypoint(ctx: JobContext):

    # Log connection attempt
    logger.info(f"Միանում ենք room-ին: {ctx.room.name}")

    # Connect to LiveKit room (audio only)
    await ctx.connect(
    url=LIVEKIT_URL,                # URL from your .env
    api_key=LIVEKIT_API_KEY,        # your key
    api_secret=LIVEKIT_API_SECRET,  # your secret
    auto_subscribe=AutoSubscribe.AUDIO_ONLY
    )

    # Wait until a user joins
    participant = await ctx.wait_for_participant()
    logger.info(f"Օգտատեր միացավ: {participant.identity}")

    # Memory for conversation (last 10 messages)
    memory = ConversationMemory(max_messages=10)

    # Metrics tracking (performance monitoring)
    metrics = SessionMetrics()

    # ============================================================
    # CREATE AI SESSION (CORE PIPELINE)
    # ============================================================

    session = AgentSession(

        #  Speech-to-Text (User voice → text)
        # (kept as you requested)
        stt=openai.STT(model="whisper-1", language="hy"),

        #  LLM (text → response)
        llm=openai.LLM(
            model="gpt-4o-mini",
            temperature=0.3  # low = more stable answers
        ),

        #  Text-to-Speech (response → voice)
        tts=openai.TTS(
            model="gpt-4o-mini-tts",
            voice="onyx"
        ),

        # Voice Activity Detection (detects when user speaks)
        vad=silero.VAD.load(
            min_speech_duration=0.4,
            min_silence_duration=0.7
        ),
    )
    # Set preemptive generation lead time to reduce mis-triggering
    session.preemptive_lead_time = 0.5  
    # ============================================================
    # SPEAKING CONTROL (PREVENT SELF-LOOP)
    # ============================================================

    # This flag tells us if agent is currently speaking
    is_agent_speaking = False


    # ============================================================
    # USER SPEECH EVENT
    # ============================================================

    @session.on("user_speech_committed")
    def on_user_speech(event):
        nonlocal is_agent_speaking

        # If agent is speaking → ignore input (prevents echo loop)
        if is_agent_speaking:
            logger.info("Ignored user speech (agent speaking)")
            return

        # Get what user said
        text = event.transcript

        # Save to memory
        memory.add("user", text)

        # Log it
        logger.info(f"User: {text}")


    # ============================================================
    # AGENT SPEECH EVENT
    # ============================================================

    @session.on("agent_speech_committed")
    def on_agent_speech(event):
        nonlocal is_agent_speaking

        # Get what agent said
        text = event.agent_transcript

        # Check confidence / clean output
        checked = check_confidence(text)

        # Save to memory
        memory.add("assistant", checked)

        # Log shortened version
        logger.info(f"Agent: {checked[:100]}...")

        # Mark agent as finished speaking
        is_agent_speaking = False


    # ============================================================
    # METRICS EVENT (PERFORMANCE TRACKING)
    # ============================================================

    @session.on("metrics_collected")
    def on_metrics(event):
        m = event.metrics

        # Create structured metrics object
        turn = TurnMetrics(
            stt_duration=getattr(m, "stt_duration", 0.0),
            llm_duration=getattr(m, "llm_duration", 0.0),
            tts_duration=getattr(m, "tts_duration", 0.0),
            total_duration=getattr(m, "total_duration", 0.0),
        )

        # Save metrics
        metrics.add_turn(turn)


    # ============================================================
    # START THE AGENT
    # ============================================================

    await session.start(
        room=ctx.room,
        agent=Agent(instructions=SYSTEM_PROMPT),
    )

    logger.info("Agent գործարկված է")


    # ============================================================
    # GREETING MESSAGE (FIRST SPEECH)
    # ============================================================

    # Mark agent as speaking BEFORE speaking
    is_agent_speaking = True

    await session.say(
        "Բարև։ <break time='400ms'/> Ես Արամն եմ։ "
        "<break time='400ms'/> Ձեր բանկային օգնականը։ "
        "<break time='500ms'/> Ինչո՞վ կարող եմ օգնել։"
    )


    # ============================================================
    # MONITOR USER (DISCONNECT HANDLER)
    # ============================================================

    # Runs in background → stops agent if user leaves
    asyncio.ensure_future(
        monitor_participant(ctx, session, metrics, participant)
    )


    # ============================================================
    # KEEP AGENT RUNNING
    # ============================================================

    # Keep session alive for 1 hour
    await asyncio.sleep(3600)


# ================================================================
# RUN THE AGENT
# ================================================================

if __name__ == "__main__":

    # Start the LiveKit worker
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            agent_name="armenian-bank-agent",
            api_key=LIVEKIT_API_KEY,
            api_secret=LIVEKIT_API_SECRET
        )
    )