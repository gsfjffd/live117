_raw_urls = """
https://www.cricbuzz.com/live-cricket-scores/162797/mlrw-vs-adsw-13th-match-womens-big-bash-league-2026
"""

MANUAL_TARGET_URLS = [url.strip() for url in _raw_urls.strip().splitlines() if url.strip()]
