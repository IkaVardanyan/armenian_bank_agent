from livekit.agents import llm

# ------------------------------------------------------------
# ConversationMemory class
# ------------------------------------------------------------
class ConversationMemory:
    """
    Keeps track of the last N messages in a conversation.
    Useful for building context for the LLM.
    """

    def __init__(self, max_messages: int = 10):
        """
        Initialize memory with a maximum number of messages.
        :param max_messages: Maximum number of messages to store
        """
        self.max_messages = max_messages
        self.messages = []  # List of messages as dicts {"role": str, "text": str}

    def add(self, role: str, text: str):
        """
        Add a new message to memory.
        :param role: 'user' or 'assistant' or 'system'
        :param text: Message text
        """
        self.messages.append({"role": role, "text": text})
        # Remove oldest message if we exceed max_messages
        if len(self.messages) > self.max_messages:
            self.messages.pop(0)

    def build_context(self, system_prompt: str) -> llm.ChatContext:
        """
        Build a ChatContext object for the LLM including system prompt
        and all stored messages.
        :param system_prompt: The initial system instructions
        :return: llm.ChatContext instance
        """
        ctx = llm.ChatContext().append(role="system", text=system_prompt)
        for msg in self.messages:
            ctx.append(role=msg["role"], text=msg["text"])
        return ctx

    def clear(self):
        """
        Clear all messages from memory.
        """
        self.messages = []

    def __len__(self):
        """
        Return the number of messages currently stored.
        """
        return len(self.messages)