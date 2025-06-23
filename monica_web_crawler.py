# scraped Monica API documentation and saved it to a text file with this.

import requests
from bs4 import BeautifulSoup
import time

BASE_URL = "https://www.monicahq.com"
API_DOC_URL = f"{BASE_URL}/api"
OUTPUT_FILE = "monica_api_documentation.txt"
HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

def get_full_page_text(url):
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        for tag in soup(["script", "style"]):
            tag.decompose()
        text = soup.get_text(separator="\n")
        lines = [line.strip() for line in text.splitlines()]
        return '\n'.join(line for line in lines if line)
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return ""

def get_subpage_links():
    slugs = [
        "activities", "activity-types", "activity-type-categories", "addresses", "audit-logs",
        "calls", "companies", "compliance", "contacts", "contact-fields", "contact-field-types",
        "conversations", "countries", "currencies", "debts", "documents", "genders", "gifts",
        "groups", "journal-entries", "notes", "occupations", "photos", "relationships",
        "relationship-types", "relationship-type-groups", "reminders", "tags", "tasks", "user"
    ]
    return [(slug.replace('-', ' ').title(), f"{BASE_URL}/api/{slug}") for slug in slugs]

def crawl_and_save():
    print(f"Fetching: {API_DOC_URL}")
    pages = [("Overview", API_DOC_URL)] + get_subpage_links()
    with open(OUTPUT_FILE, "w", encoding="utf-8") as file:
        for title, url in pages:
            print(f"Saving section: {title} ({url})")
            text = get_full_page_text(url)
            file.write(f"\n{'='*80}\n{title}\n{'='*80}\n\n{text}\n\n")
            time.sleep(1)
    print(f"Done. Documentation saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    crawl_and_save()
