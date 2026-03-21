import asyncio
import logging
import time

# Logger for this agent
logger = logging.getLogger("armenian-bank-agent")

# ------------------------------------------------------------
# Shutdown helper
# ------------------------------------------------------------
async def shutdown(session, metrics, reason: str = "normal"):
    """
    Gracefully stop the agent, say a farewell message, and log metrics.

    Args:
        session: The AgentSession object (used for TTS).
        metrics: SessionMetrics object for summarizing performance.
        reason (str): Reason for shutdown: "normal", "timeout", or "error".
    """
    logger.info(f" Shutdown started — reason: {reason}")
    try:
        if reason == "normal":
            # Normal end of conversation
            await session.say(
                "Շնորհակալություն, որ կապվեցիք մեզ հետ։ Հաջող օր։",
                allow_interruptions=False,
            )
        elif reason == "timeout":
            # User inactive too long
            await session.say(
                "Կապն ընդհատվեց անգործության պատճառով։ Հաջող օր։",
                allow_interruptions=False,
            )
        elif reason == "error":
            # Technical error occurred
            await session.say(
                "Կներեք, տեխնիկական խնդիր առաջացավ։ Խնդրում ենք կրկին կապվել։",
                allow_interruptions=False,
            )
    except Exception as e:
        # Catch TTS errors or other issues during shutdown
        logger.error(f" Error during shutdown: {e}")
    finally:
        # Summarize session metrics and mark agent as closed
        metrics.summary()
        logger.info(" Agent shutdown completed")


# ------------------------------------------------------------
# Monitor participant activity
# ------------------------------------------------------------
async def monitor_participant(ctx, session, metrics, participant):
    """
    Background task to monitor if the user is still in the room.
    Stops the agent if user leaves or inactivity timeout is reached.

    Args:
        ctx: JobContext object containing the room info.
        session: AgentSession object.
        metrics: SessionMetrics object.
        participant: The participant object to monitor.
    """
    INACTIVITY_TIMEOUT = 600  # 10 minutes in seconds

    while True:
        await asyncio.sleep(10)  # Check every 10 seconds

        # Check if participant left the room
        if participant.identity not in [
            p.identity for p in ctx.room.remote_participants.values()
        ]:
            logger.info(" User left the room")
            await shutdown(session, metrics, reason="normal")
            break

        # Check inactivity timeout
        if time.time() - metrics.session_start > INACTIVITY_TIMEOUT:
            logger.warning(" Inactivity timeout reached")
            await shutdown(session, metrics, reason="timeout")
            break