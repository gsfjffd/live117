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
            page.goto(source_url, timeout=40000)
            page.wait_for_timeout(7000) # SPA load hone ke liye thoda aur wait
            
            page_text = page.evaluate("() => document.body.innerText")
            lines = [l.strip() for l in page_text.split('\n') if l.strip()]
            
            current_score = "Score updating..."
            ball_event = "Match live in progress..."

            # 1. Smart Search: Poori page text mein score format (jaise 145/4 ya overs) dhoondhein
            score_candidates = []
            for line in lines:
                if re.search(r'\d+/\d+', line) and len(line) < 45:
                    score_candidates.append(line)
            
            if score_candidates:
                current_score = score_candidates[0]
            else:
                # Fallback: Agar slash wala score na mile toh match-related keywords dhoondhein
                for line in lines:
                    if any(w in line.lower() for w in ["run", "ov", "target", "need", "lead", "v/s"]) and len(line) < 50:
                        current_score = line
                        break

            # 2. Smart Commentary Search: Latest event ya commentary dhoondhein
            commentary_candidates = []
            for line in lines:
                if any(w in line.lower() for w in ["four", "six", "wicket", "out", "runs", "extras", "wide", "to"]):
                    if len(line) > 10 and len(line) < 120 and line != current_score:
                        commentary_candidates.append(line)
            
            if commentary_candidates:
                ball_event = commentary_candidates[0]

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
