_raw_urls = """
https://third-party-cricket-site.com/match/upcoming-match-1
https://third-party-cricket-site.com/match/upcoming-match-2
"""

MANUAL_TARGET_URLS = [url.strip() for url in _raw_urls.strip().splitlines() if url.strip()]
