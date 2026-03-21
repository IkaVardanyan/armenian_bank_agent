# ================================================================
# load_data.py
# ================================================================

import json
import os
import re

# ================================================================
# SETTINGS / CONSTANTS
# ================================================================

# Base directory where bank JSON files are stored
BASE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bank_data")

# Bank names in phonetic Armenian for TTS purposes
BANK_NAMES = {
    "amio":   "Ամիո Բանկ",
    "ameria": "Ամերիա Բանկ",
    "fast":   "Ֆասթ Բանկ"
}

# Currency names in Armenian phonetic representation
CURRENCY_NAMES = {
    "usd": "դոլար",
    "usdt": "յուսդիթի",
    "eur": "եվրո"
}

# ================================================================
# HELPER FUNCTIONS
# ================================================================

def convert_numbers_and_currency(text: str) -> str:
    """
    Convert numbers and currency abbreviations to phonetic Armenian.
    Currently keeps numbers as digits; currency codes are replaced.
    """
    # Replace currency codes with Armenian phonetic
    def currency_repl(m):
        cur = m.group(0).lower()
        return CURRENCY_NAMES.get(cur, cur)
    text = re.sub(r"\b(usdt|usd|eur)\b", currency_repl, text, flags=re.IGNORECASE)

    # Replace numbers if needed (currently keeps as digits)
    def number_repl(m):
        num = m.group(0)
        # TODO: Optional: convert 1000 → "հազար" etc. for full TTS pronunciation
        return num
    text = re.sub(r"\d+(\.\d+)?", number_repl, text)

    return text

# ================================================================
# MAIN FUNCTION
# ================================================================

def load_bank_data() -> str:
    """
    Load all bank data and format it for TTS-friendly Armenian reading.
    Combines loans, deposits, and branches for all banks.
    """
    all_data = ""
    for bank_key, bank_name in BANK_NAMES.items():
        path = os.path.join(BASE_DIR, f"{bank_key}.json")
        if not os.path.exists(path):
            print(f"{bank_name} file not found — {path}")
            continue

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Add bank name as header
        all_data += f"\n\n=== {bank_name} ===\n"

        # Loans section
        loans_text = convert_numbers_and_currency(data.get("loans", ""))
        all_data += f"\n[LOANS]\n{loans_text}\n"

        # Deposits section
        deposits_text = convert_numbers_and_currency(data.get("deposits", ""))
        all_data += f"\n[DEPOSITS]\n{deposits_text}\n"

        # Branches section
        branches_text = convert_numbers_and_currency(data.get("branches", ""))
        all_data += f"\n[BRANCHES]\n{branches_text}\n"

    return all_data

# ================================================================
# QUICK TEST (optional)
# ================================================================

if __name__ == "__main__":
    text = load_bank_data()
    print(text[:1000])  # Print first 1000 characters for quick check