import logging

# Create a logger for the agent
logger = logging.getLogger("armenian-bank-agent")

# Set of Armenian characters to detect Armenian text
ARMENIAN_CHARS = set("աբգդեզէըթժիլխծկհձղճմջռսվտրցւփքօֆ")

# Default response when input is not in Armenian
NON_ARMENIAN_RESPONSE = (
    "Կներեք, ես աշխատում եմ միայն հայերեն։ "
    "Ես կարող եմ օգնել վարկերի, ավանդների և մասնաճյուղերի վերաբերյալ հարցերով։ "
    "Խնդրում եմ դիմեք հայերեն։"
)

def detect_language(text: str) -> str:
    """
    Detect the language of a given text.
    
    - Returns 'hy' for Armenian if more than 50% of letters are Armenian.
    - Returns 'ru' if any Cyrillic characters are found.
    - Returns 'en' for English or unknown otherwise.
    
    :param text: The input string
    :return: Language code: 'hy', 'ru', 'en', or 'unknown'
    """
    if not text:
        return "unknown"

    text_lower = text.lower()

    # Count Armenian letters in the text
    armenian_count = sum(1 for char in text_lower if char in ARMENIAN_CHARS)
    # Count total alphabetic characters
    total_letters = sum(1 for char in text_lower if char.isalpha())

    if total_letters == 0:
        return "unknown"

    # Calculate ratio of Armenian letters
    armenian_ratio = armenian_count / total_letters

    if armenian_ratio > 0.5:
        return "hy"  # Mostly Armenian
    elif any(char in text_lower for char in "абвгдеёжзийклмнопрстуфхцчшщъыьэюя"):
        return "ru"  # Cyrillic detected → Russian
    else:
        return "en"  # Default fallback to English