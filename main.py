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
            page.wait_for_timeout(5000)
            
            current_score = None
            
            # 1. Direct Cricbuzz element target karo
            try:
                score_elem = page.locator(".cb-min-st-rw, .cb-scrd-hdr-rw, .cb-min-score").first
                if score_elem.count() > 0:
                    current_score = score_elem.inner_text().strip()
            except Exception:
                pass

            page_text = page.evaluate("() => document.body.innerText")

            # 2. Agar element nahi mila toh flexible regex lagao
            if not current_score or len(current_score) < 3:
                # Matches patterns like 125/4 (15.2) or similar score lines
                score_matches = re.findall(r'(\d+/\d+\s*\([^)]+\))', page_text)
                if score_matches:
                    current_score = score_matches[0]
                else:
                    num_matches = re.findall(r'\b\d{1,3}/\d{1,2}\b', page_text)
                    current_score = num_matches[0] if num_matches else "Live Match Running"

            # 3. Commentary / Latest event extract karo
            lines = [line.strip() for line in page_text.split('\n') if line.strip()]
            ball_event = "Match in progress..."
            for line in lines:
                if any(kw in line.lower() for kw in ["four", "six", "wicket", "out", "runs", "ov", "to", "c & b"]):
                    if len(line) > 8 and len(line) < 140:
                        ball_event = line
                        break

            browser.close()
            return {
                "source_url": source_url,
                "score_summary": {"current_score": current_score},
                "latest_commentary": {"ball_event": ball_event}
            }
        except Exception as e:
            print(f"Scraping error: {e}")
            browser.close()
            return None

def run_pipeline():
    print("--- Pipeline Started ---")
    matches_data = []

    for url in MANUAL_TARGET_URLS:
        data = scrape_match_data(url)
        if data:
            matches_data.append(data)
        time.sleep(2)

    payload = {
        "timestamp": datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC'),
        "total_matches": len(matches_data),
        "matches": matches_data
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=4)
    print("Data saved successfully.")

if __name__ == "__main__":
    run_pipeline()
