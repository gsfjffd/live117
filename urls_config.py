_raw_urls = """
https://www.fancode.com/cricket/tour/west-indies-tour-of-bangladesh-2026-19985462/matches/west-indies-vs-bangladesh-4250527/commentary
https://www.cricinfo.com/live-cricket-score
https://crex.com/
"""

MANUAL_TARGET_URLS = [url.strip() for url in _raw_urls.strip().splitlines() if url.strip()]
