import logging
import openai as openai_errors
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

# Create a logger for the agent
logger = logging.getLogger("armenian-bank-agent")

# Predefined Armenian responses for different error types
ERROR_RESPONSES = {
    "api_error": (
        "Կներեք, կապի խնդիր կա։ "
        "Խնդրում եմ մի պահ սպասեք և կրկնեք հարցը։"
    ),
    "timeout": (
        "Կներեք, պատասխանը ուշանում է։ "
        "Խնդրում եմ կրկնեք հարցը։"
    ),
    "rate_limit": (
        "Կներեք, համակարգը ծանրաբեռնված է։ "
        "Խնդրում եմ մի քանի վայրկյան հետո կրկնեք։"
    ),
    "unknown": (
        "Կներեք, անսպասելի խնդիր առաջացավ։ "
        "Խնդրում եմ կրկնել կամ ուղղակի բանկ դիմել։"
    ),
}

# -------------------------------
# Safe LLM Call with Automatic Retry
# -------------------------------
@retry(
    stop=stop_after_attempt(3),  # Retry up to 3 times
    wait=wait_exponential(multiplier=1, min=1, max=4),  # Exponential backoff
    retry=retry_if_exception_type(Exception),  # Retry on any exception
    reraise=True,  # Reraise exception if all retries fail
)
async def safe_llm_call(llm_model, chat_ctx):
    """
    Call the LLM safely with retries.
    
    :param llm_model: The LiveKit LLM model instance
    :param chat_ctx: The ChatContext for conversation
    :return: LLM response
    """
    return await llm_model.chat(chat_ctx=chat_ctx)

# -------------------------------
# Handle Errors and Respond to User
# -------------------------------
async def handle_error(error: Exception, agent, metrics) -> bool:
    """
    Handle exceptions during LLM calls or agent operations.
    Sends a user-friendly Armenian response, logs the error, 
    and shuts down the agent if needed.

    :param error: The exception instance
    :param agent: The LiveKit agent session
    :param metrics: Session metrics instance
    :return: True if handled successfully, False if agent shutdown
    """
    # Log the error details
    logger.error(f" Սխալ: {type(error).__name__} — {error}")

    # Classify the error type
    if isinstance(error, openai_errors.RateLimitError):
        error_type = "rate_limit"
    elif isinstance(error, openai_errors.APITimeoutError):
        error_type = "timeout"
    elif isinstance(error, openai_errors.APIError):
        error_type = "api_error"
    else:
        error_type = "unknown"

    try:
        # Inform the user in Armenian
        await agent.say(ERROR_RESPONSES[error_type], allow_interruptions=False)
        return True
    except Exception as e:
        # Critical error: log and shut down agent
        logger.critical(f"Critical error: {e}")
        from utils.shutdown import shutdown
        await shutdown(agent, metrics, reason="error")
        return False