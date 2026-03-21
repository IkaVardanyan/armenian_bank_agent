import requests
from bs4 import BeautifulSoup
import json
import os
import time

# ---- Config ----
# Directory where scraped bank JSON files will be saved
BASE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bank_data")

# ---- Bank URLs ----
# Mapping of bank keys to their specific URLs for loans, deposits, and branches
BANKS = {
    "amio": {
        "loans":     "https://www.amiobank.am/en/loans",
        "deposits":  "https://www.amiobank.am/en/deposits",
        "branches":  "https://www.amiobank.am/en/offices"
    },
    "ameria": {
        "loans":     "https://www.ameriabank.am/en/personal/loans",
        "deposits":  "https://www.ameriabank.am/en/personal/deposits",
        "branches":  "https://www.ameriabank.am/en/branches"
    },
    "fast": {
        "loans":     "https://www.fastbank.am/en/individual/loans",
        "deposits":  "https://www.fastbank.am/en/individual/deposits",
        "branches":  "https://www.fastbank.am/en/branches"
    }
}

# ---- Helper function ----
def scrape_page(url):
    """
    Scrape a single page and extract visible text.

    Arguments:
        url (str): The page URL to scrape.

    Returns:
        str: Cleaned page text or empty string if error occurs.
    """
    try:
        # Set User-Agent to avoid bot blocking
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()  # Raise error for bad HTTP status

        # Parse HTML content
        soup = BeautifulSoup(response.text, "html.parser")

        # Remove navigation, header, footer, script, and style tags
        for tag in soup(["nav", "footer", "script", "style", "header"]):
            tag.decompose()

        # Extract visible text with spaces
        text = soup.get_text(separator=" ", strip=True)
        return text

    except Exception as e:
        # Print error but continue scraping other pages
        print(f" Սխալ {url} — {e}")
        return ""


# ---- Main scraping function ----
def scrape_all_banks():
    """
    Scrape all banks' loans, deposits, and branch info.
    Save results as JSON files in BASE_DIR.
    """
    # Ensure the data directory exists
    os.makedirs(BASE_DIR, exist_ok=True)

    for bank_name, pages in BANKS.items():
        print(f"\n Scraping {bank_name}...")

        # Initialize dictionary to store scraped content
        bank_data = {
            "bank": bank_name,
            "loans": "",
            "deposits": "",
            "branches": ""
        }

        # Scrape each page for the bank
        for topic, url in pages.items():
            print(f"   {topic} — {url}")
            text = scrape_page(url)
            bank_data[topic] = text

            # Pause between requests to avoid overloading server
            time.sleep(1)

        # Save the bank data to a JSON file
        output_path = f"{BASE_DIR}/{bank_name}.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(bank_data, f, ensure_ascii=False, indent=2)

        print(f"  Պահված — {output_path}")


# ---- Script entry point ----
if __name__ == "__main__":
    print(" Սկսում ենք scraping...")
    scrape_all_banks()
    print("\n Ամեն ինչ պատրաստ է!")

    # Print created files and their sizes
    print("\n Ստեղծված ֆայլեր:")
    for f in os.listdir(BASE_DIR):
        path = f"{BASE_DIR}/{f}"
        size = os.path.getsize(path)
        print(f"  {f} — {size} bytes")