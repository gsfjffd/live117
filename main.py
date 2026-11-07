import os
import json
import time
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
            print(f"Opening URL: {source_url}")
            page.goto(source_url, timeout=30000)
            page.wait_for_timeout(5000)
            
            # Page ka title aur body text nikalna
            page_title = page.title()
            page_text = page.evaluate("() => document.body.innerText")
            
            print(f"Page Title: {page_title}")
            
            # Agar Cloudflare ya Access Denied hai
            if "Access Denied" in page_text or "Cloudflare" in page_text or "Blocked" in page_title:
                score = "Blocked by Cricbuzz Security!"
                commentary = "GitHub Server IP is blocked by Cricbuzz."
            else:
                score = f"Loaded Title: {page_title[:30]}"
                commentary = page_text[:100].replace('\n', ' ')

            browser.close()
            return {
                "source_url": source_url,
                "score_summary": {"current_score": score},
                "latest_commentary": {"ball_event": commentary}
            }
        except Exception as e:
            print(f"Error: {e}")
            browser.close()
            return {
                "source_url": source_url,
                "score_summary": {"current_score": "Connection Failed"},
                "latest_commentary": {"ball_event": str(e)[:100]}
            }

def run_pipeline():
    matches_data = []
    for url in MANUAL_TARGET_URLS:
        data = scrape_match_data(url)
        if data:
            matches_data.append(data)

    payload = {
        "timestamp": datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC'),
        "total_matches": len(matches_data),
        "matches": matches_data
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=4)
    print("Saved to JSON.")

if __name__ == "__main__":
    run_pipeline()
