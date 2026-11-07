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
        # Cricbuzz ke anti-bot block ko bypass karne ke liye arguments
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-setuid-sandbox"
            ]
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800}
        )
        page = context.new_page()
        
        try:
            print(f"Fetching Cricbuzz URL: {source_url}")
            page.goto(source_url, timeout=40000, wait_until="domcontentloaded")
            page.wait_for_timeout(6000) # Score load hone ke liye thoda wait karein
            
            # Poore page ka text nikalna
            page_text = page.evaluate("() => document.body.innerText")
            
            if not page_text or len(page_text) < 100:
                print(f"Blocked or empty page for {source_url}")
                browser.close()
                return None

            # Score dhundhne ke liye smart pattern matching (Regex)
            score_match = re.search(r'(\d+/\d+)\s*\((\d+(?:\.\d+)?)\s*ov\)', page_text)
            if score_match:
                current_score = f"{score_match.group(1)} ({score_match.group(2)} ov)"
            else:
                current_score = "Live Match (Score syncing...)"

            # Commentary ya latest event nikalna
            lines = [line.strip() for line in page_text.split('\n') if line.strip()]
            ball_event = "Match in progress..."
            for i, line in enumerate(lines):
                if "ov" in line.lower() or "runs" in line.lower() or "four" in line.lower() or "six" in line.lower() or "out" in line.lower():
                    if i + 1 < len(lines):
                        ball_event = lines[i+1]
                        break

            browser.close()
            return {
                "source_url": source_url,
                "score_summary": {"current_score": current_score},
                "latest_commentary": {"ball_event": ball_event}
            }
        except Exception as e:
            print(f"Scraping error for {source_url}: {e}")
            browser.close()
            return None

def run_pipeline():
    print("--- Cricbuzz Scraper Pipeline Started ---")
    matches_data = []

    for url in MANUAL_TARGET_URLS:
        data = scrape_match_data(url)
        if data:
            matches_data.append(data)
        time.sleep(random.uniform(2.0, 4.0))

    payload = {
        "timestamp": datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC'),
        "total_matches": len(matches_data),
        "matches": matches_data
    }

    with open(OUTPUT_FILE, "w") as f:
        json.dump(payload, f, indent=4)
    print("Data successfully saved to live_data.json")

if __name__ == "__main__":
    run_pipeline()
