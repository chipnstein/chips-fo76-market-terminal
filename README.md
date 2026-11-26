# Fallout 76 Market Terminal (`r/Market76`)

A personal, non-commercial, self-hosted market analytics dashboard for the *Fallout 76* trading community (`r/Market76`). It aggregates standardized public trade post titles across **PC**, **PlayStation**, and **Xbox** to visualize supply-vs-demand ratios, price spreads, and historical market trends.

## Overview

`r/Market76` uses structured trade post titles (e.g., `[PC] H: 500 Leaders W: Glowing Mask` or `[PS] H: Weenie Wagon Plan W: 20k Caps`). This project parses those public titles into a local SQLite database to track:

- **Supply vs. Demand (`H:` vs. `W:`):** Ratio of sellers to buyers for specific items.
- **Price Spreads & Trends:** Historical asking and offering ranges in in-game currencies (Caps and Leader Bobbleheads).
- **Platform Separation:** Dedicated views for PC, PlayStation, and Xbox markets.

## Reddit Data API Compliance

This project is built to comply with Reddit's Data API Terms and Responsible Builder Policy:

- **Strictly Read-Only:** Performs **no** posting, commenting, voting, messaging, or moderation actions.
- **Low Call Volume:** Polls `r/Market76/new` once every 15 minutes (~96 requests/day), well within the 100 QPM free-tier limit, and respects `X-Ratelimit-Remaining` / `X-Ratelimit-Reset` headers.
- **No User Data or Raw Content Storage:** Extracts only anonymized market metrics (platform, trade direction, item name, currency, numeric price, and timestamp). Reddit usernames, user profiles, and raw post bodies are **not** stored.
- **Non-Commercial & No AI/ML:** Strictly for personal, non-commercial use. No ads, no monetization, no data redistribution, and no AI/machine learning training.

## Project Architecture

```text
fo76-market-terminal/
├── collectors/
│   ├── reddit_collector.py  # Read-only OAuth2 collector for r/Market76
│   └── parser.py            # Parses platform, H:/W: direction, item, and price
├── database/
│   └── db_manager.py        # SQLite schema management, deduplication, and queries
├── dashboard/
│   └── app.py               # Local web dashboard (PC / PS / Xbox tabs)
├── data/                    # Local SQLite database (gitignored)
├── config.py                # Polling interval, currencies, and platform tags
├── run_collector.py         # Entry point for the background polling loop
└── requirements.txt         # Python dependencies
```

## Setup (Local Development)

1. Create and activate a Python virtual environment:
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2. Create a `.env` file (gitignored) with your approved Reddit OAuth2 script credentials:
```env
REDDIT_CLIENT_ID=your_client_id
REDDIT_CLIENT_SECRET=your_client_secret
REDDIT_USER_AGENT=python:fo76-market-terminal:v0.1 (by /u/your_username)
```

3. Run the collector:
```powershell
python run_collector.py
```

4. Launch the local dashboard:
```powershell
streamlit run dashboard/app.py
```