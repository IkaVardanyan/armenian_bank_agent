import time
import logging
from dataclasses import dataclass, field
from typing import List

# Logger for session metrics
logger = logging.getLogger("armenian-bank-agent")


# ------------------------------------------------------------
# Single turn metrics
# ------------------------------------------------------------
@dataclass
class TurnMetrics:
    """
    Stores timing and text information for a single conversational turn.
    """
    stt_duration: float = 0.0     # Time taken for Speech-to-Text
    llm_duration: float = 0.0     # Time taken for LLM to generate response
    tts_duration: float = 0.0     # Time taken for Text-to-Speech
    total_duration: float = 0.0   # Total time for the turn
    user_text: str = ""           # User's spoken text
    agent_text: str = ""          # Agent's response text


# ------------------------------------------------------------
# Full session metrics
# ------------------------------------------------------------
@dataclass
class SessionMetrics:
    """
    Tracks all turns in a session and computes summary statistics.
    """
    turns: List[TurnMetrics] = field(default_factory=list)  # List of all turns
    session_start: float = field(default_factory=time.time)  # Start time of session

    # Add a new turn to the session
    def add_turn(self, turn: TurnMetrics):
        self.turns.append(turn)
       
    # Summarize session metrics and log averages
    def summary(self):
        if not self.turns:
            return

        avg_total = sum(t.total_duration for t in self.turns) / len(self.turns)
        avg_stt   = sum(t.stt_duration   for t in self.turns) / len(self.turns)
        avg_llm   = sum(t.llm_duration   for t in self.turns) / len(self.turns)
        avg_tts   = sum(t.tts_duration   for t in self.turns) / len(self.turns)
        session_duration = time.time() - self.session_start

        # Log summary with Armenian labels
        logger.info(
            f"Session summary | "
            f"Turns: {len(self.turns)} | "
            f"Duration: {session_duration:.1f}s | "
            f"Avg STT: {avg_stt:.2f}s | "
            f"Avg LLM: {avg_llm:.2f}s | "
            f"Avg TTS: {avg_tts:.2f}s | "
            f"Avg Total: {avg_total:.2f}s"
        )