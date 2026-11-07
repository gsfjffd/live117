import os
import json
import time
import random
import re
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
            page.goto(source_url, timeout=45000)
            page.wait_for_timeout(8000) # Full dynamic content load hone ke liye
            
            page_text = page.evaluate("() => document.body.innerText")
            lines = [l.strip() for l in page_text.split('\n'] if l.strip()]
            
            current_score = "Live Match Running"
            commentary_list = []

            # 1. Score / Overs dhoondhne ke liye smart search
            for line in lines:
                if (re.search(r'\d+/\d+', line) or "ov" in line.lower() or "target" in line.lower()) and len(line) < 50:
                    current_score = line
                    break

            # 2. Ball-by-ball commentary lines extract karna
            for line in lines:
                # Commentary mein overs (jaise 19.4, 18.2) ya cricket terms hote hain
                if re.search(r'\b\d{1,2}\.\d\b', line) or any(term in line.lower() for term in ["four", "six", "wicket", "out", "1 run", "2 runs", "3 runs", "dot", "extras", "wide"]):
                    if len(line) > 8 and len(line) < 150 and line not in commentary_list:
                        commentary_list.append(line)

            # Agar commentary list khali ho toh fallback messages daal dein
            if not commentary_list:
                commentary_list = ["Match commentary syncing from source..."]

            browser.close()
            return {
                "source_url": source_url,
                "score_summary": {"current_score": current_score},
                "latest_commentary": {"ball_event": commentary_list[:5]} # Top 5 recent commentary items
            }
        except Exception as e:
            print(f"Error scraping {source_url}: {e}")
            browser.close()
            return {
                "source_url": source_url,
                "score_summary": {"current_score": "Error fetching score"},
                "latest_commentary": {"ball_event": [str(e)[:80]]}
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
    print(f"Successfully saved {len(matches_data)} matches.")

if __name__ == "__main__":
    run_pipeline()
