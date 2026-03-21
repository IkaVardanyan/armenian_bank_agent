import logging

# Logger for tracking warnings or info
logger = logging.getLogger("armenian-bank-agent")

# Keywords that indicate GPT is uncertain about its response
# Includes Armenian, English, and Russian expressions
UNCERTAIN_KEYWORDS = [
    "կարծում եմ",   
    "հավանաբար",    
    "մոտավորապես", 
    "վստահ չեմ",   
    "think",        
    "probably",     
    "maybe",        
    "не уверен",    
]

# Disclaimer to append if the response is uncertain
UNCERTAINTY_DISCLAIMER = (
    " Խնդրում եմ հաստատեք այս տեղեկությունը "
    "անմիջականորեն բանկի հետ կապվելով։"
)

def check_confidence(response_text: str) -> str:
    """
    Checks if the AI response contains uncertain keywords.
    If found, appends a disclaimer advising the user to verify with the bank.
    
    Args:
        response_text (str): The AI-generated response.
    
    Returns:
        str: Either the original response or the response with a disclaimer.
    """
    # Normalize text for comparison
    response_lower = response_text.lower()
    
    # Check if any uncertain keyword is present
    is_uncertain = any(
        keyword in response_lower
        for keyword in UNCERTAIN_KEYWORDS
    )
    
    if is_uncertain:
        # Log a warning that the AI is uncertain
        logger.warning("GPT-ը անվստահ պատասխան տվեց")
        # Append disclaimer to inform user
        return response_text + UNCERTAINTY_DISCLAIMER
    
    # Return the original response if confident
    return response_text