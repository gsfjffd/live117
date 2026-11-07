import os
import json
import time
import random
from datetime import datetime
from playwright.sync_api import sync_playwright
from urls_config import MANUAL_TARGET_URLS

OUTPUT_FILE = "live_data.json"

def scrape_match_data(source_url):
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"]
        )
        page = browser.new_page()
        try:
            print(f"Scraping URL: {source_url}")
            page.goto(source_url, timeout=30000)
            page.wait_for_timeout(4000)
            
            # Page ka text nikalna
            page_text = page.evaluate("() => document.body.innerText")
            lines = [l.strip() for l in page_text.split('\n') if l.strip()]
            
            # Sample parsing logic (Aap apne target site ke hisab se text utha sakte hain)
            current_score = lines[0] if len(lines) > 0 else "Score not found"
            ball_event = lines[1] if len(lines) > 1 else "Match live..."

            browser.close()
            return {
                "source_url": source_url,
                "score_summary": {"current_score": current_score},
                "latest_commentary": {"ball_event": ball_event}
            }
        except Exception as e:
            print(f"Error scraping {source_url}: {e}")
            browser.close()
            return {
                "source_url": source_url,
                "score_summary": {"current_score": "Error fetching score"},
                "latest_commentary": {"ball_event": str(e)[:80]}
            }

def run_pipeline():
    matches_data = []
    for url in MANUAL_TARGET_URLS:
        data = scrape_match_data(url)
        if data:
            matches_data.append(data)
        time.sleep(random.uniform(1.0, 2.0))

    payload = {
        "timestamp": datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC'),
        "total_matches": len(matches_data),
        "matches": matches_data
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=4)
    print(f"Successfully saved {len(matches_data)} matches to live_data.json")

if __name__ == "__main__":
    run_pipeline()
