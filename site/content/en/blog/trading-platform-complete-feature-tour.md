---
title: "A Complete Feature Tour of the Trading Platform"
date: 2026-08-30
draft: false
description: "Every screener, scanner, dashboard page, and broker-overlay feature across the three repositories behind a solo-built market-intelligence system for NSE/BSE equities — tradepy, trading-client-web, and trading-client-chrome-ext."
tags: ["python", "flask", "react", "postgresql", "chrome-extension", "llm", "algorithmic-trading", "fintech"]
---

The Trading Platform is a personal, LAN-hosted market-intelligence system for Indian equities (NSE/BSE), built solo across three repositories that each do one job and stay out of each other's way:

- **tradepy** — a Python/Flask backend that owns every query, every score, and every screener. It reads a shared PostgreSQL/TimescaleDB database, runs a scheduler of nightly and intraday jobs, and exposes everything over a REST API.
- **trading-client-web** — a React/Vite dashboard, the "Tactical Cockpit," that renders that API as a dense, instrument-grade UI with 38 routes.
- **trading-client-chrome-ext** — a Chrome extension that overlays the same intelligence directly onto a broker's web platform (Fyers), plus a side quest in silently bypassing a paid fundamentals vendor's login screen.

What follows is an exhaustive tour of what each of the three actually does — every screener's real thresholds, every dashboard page, every extension feature — pulled directly from the source rather than from what the READMEs claim. A few things below are dead code or features that are wired up but not yet reachable from any UI; those are called out explicitly rather than swept under the rug, because "what's actually shipped vs. what's aspirational" is itself useful information about how a solo project like this evolves.

## The shape of the system

The three repositories are governed by a documented **API Contract**: `tradepy` owns the JSON shape of every response, and any change to a route's keys has to be mirrored by hand in the two frontends' API clients. There's no shared schema package, no codegen — just a rule, written down, that both frontend `AGENTS.md` files repeat: never hardcode an API URL, always read `VITE_API_BASE_URL` (web) or `MIX_API_URL` (extension), and treat the backend as the single source of truth for business logic. The frontends are deliberately "pure consumers" — no computation happens client-side beyond formatting.

Underneath tradepy sit **two Postgres servers**, chosen by `MAX(date)` rather than hardcoded: a live server at `192.168.1.16` that keeps only the current session for high-volume intraday tables (5-minute candles, option data), and an archive server at `192.168.1.6` holding full history. A Windows Task Scheduler job syncs the two hourly overnight, atomically enough that a mid-sync power loss just resumes from the last successful timestamp.

Every one of tradepy's ~30 Flask blueprints and every screener can be switched off independently — `GET /api/v1/features` resolves a `.env`-driven feature-flag map (`FEATURE_SCREENER_<ID>`, `FEATURE_JOB_<NAME>`, one flag per blueprint) that the frontend uses to hide nav entries for anything currently disabled. It's a deliberate replacement for the older approach of commenting code out of `server.py`.

---

## The backend: tradepy

### The API surface

`server.py` registers around 28 blueprints plus a handful of routes defined directly on the app, covering roughly twenty distinct feature domains: symbol profiles, Signal Lab, MSI fundamentals browsing, alerts, institutional flow, chart generation, insider tracking, the Live Scanner, a Cockpit aggregation layer, watchlists, Fyers broker integration, MSI daily reports, sector/subsector scoring, the legacy momentum/earnings screener, the institutional pipeline, autonomous paper trading, heatmaps, the AI research desk, Breakout Radar, dashboard rankings, the F&O desk, Market Map, the trade journal, Smart Money, a second research-analytics blueprint, and peer browsing. Every one of those is its own section below.

A global exception handler posts any unhandled 500 straight to a dedicated Telegram channel with the full traceback — added, per an in-code comment, after a stale bookmarked URL used to page the project's owner as if the whole server were down for a routine 404.

### Signal Lab: fourteen registered screeners

Signal Lab is the platform's central screener registry (`src/lib/signals/registry.py`), and it's built so that **the registry entry is the entire UI spec** — name, description, methodology text, the criteria chips, the scoring breakdown, and the result table's columns are all metadata on the Python side. Adding a new screener never touches the frontend.

| Screener | What actually gates a stock in |
|---|---|
| **Reversal Screener** | MasterScore ≥65 with a positive latest quarter, 15–60% off the 52-week high, plus at least one exhaustion signal (bullish engulfing, hammer, RSI bullish divergence, or RSI recovering above 30); ≥₹0.5 Cr median 50-day turnover, ₹500 Cr market-cap floor |
| **Big Move Stocks** | 20-day Bollinger-width in the bottom quartile of the stock's own 6-month range ("squeeze") plus volume ≥2× its 50-day average or a 4%+ single-day / 6%+ 3-day move ("expansion") |
| **Smallcap Hunter** | Below market-cap rank 250, ≥₹300 Cr floor; hard-gated on rising institutional flow (≥+0.25pp QoQ across MF+FPI+Insurance+Bank), promoter stake rising or open-market buying, EPS growth ≥20% YoY, sales growth ≥10% YoY, within 25% of the 52-week high |
| **Emerging Stocks** | Mid/small cap only (excludes the top 100 by market cap); MasterScore ≥75, EPS Strength ≥80, an in-house RS Rating ≥85, EPS growth ≥25% YoY, sales growth ≥20%, Minervini trend template ≥5 of 7 |
| **Stock Pulse** | Built from *today's* movers — circuit hits on both exchanges, volume gainers/spurts, 52-week extremes — scored into a Strong-Buy-to-Avoid verdict |
| **Stock Screener (Composite)** | A weighted 100-point core (MasterScore 35%, EPS Strength 25%, Price Strength 20%, Group Rank 10%, Buyer Demand 10%) plus up to 35 bonus points, so totals can exceed 100 |
| **RS Line Screener** | RS Line (stock vs. Nifty 50) within 3% of its own 52-week high, classified as a new high, confirmed, or a bullish divergence |
| **A/D Rating Screener** | An independently computed Accumulation/Distribution grade (A+ to E) from CLV×volume A/D-line slope, 21-day Chaikin Money Flow, delivery %, and up/down-volume streaks |
| **Smart Money Composite** | FII/MF quarterly flow (30 pts) + F&O OI buildup (20) + 30-day open-market insider buying net of ESOPs/pledges (20) + MSI Buyer Demand grade (20) + block-deal bonus (10) |
| **MSI Blue Dot + Superstar Convergence** | Four simultaneous gates: MSI weekly blue-dot RS trigger, RS Rating ≥85, MasterScore ≥70 with Buyer Demand ≥B+, at least one recognized "superstar investor" holding >1%, within 5% of the technical pivot |
| **Options Analytics Edge** | Max Pain (computed from the nearest expiry's live option chain) above spot, or PCR ≥0.9, mandatory MasterScore ≥70 (the median MasterScore across the whole F&O universe is only ~56, so 70 is roughly the top 16%) |
| **Leadership Score Composite** | RS Line (25) + EPS Strength (20) + institutional accumulation (20) + sector-relative 21-day return (15) + Buyer Demand (10) + Group Rank (10) |
| **Advanced VCP Screener** | The only hard gate is being within 40% of the 52-week high; everything else — trend template, contraction count, volume dry-up/thrust, doji count — is scored, not filtered |
| **EPS Accelerator** | Rewards *accelerating* YoY EPS growth (35 pts, the "C" in CANSLIM) plus magnitude, consistency, annual trend, forward estimates, and sales support |

Every screener is its own feature flag and writes to its own `signals_<name>` table. A **second, separate** screener system (`src/lib/screener_api.py`, `/api/v1/screener`) covers just `momentum` (EMA20/50/200 + RSI14 + ADX + ATR trend health) and `earnings` (pure reported-earnings quality, deliberately excluding any MSI-derived field — explicitly guarded against percentage-growth artifacts, since one company's +2,675% YoY EPS print off a near-zero base would otherwise dominate the list). Both write into a shared `screener_scores` table computed nightly.

All of it sits on one shared universe-building module (`src/lib/screeners/universe.py`) that stitches NSE and BSE listings together by ISIN, normalizes the well-known unit mismatch between the two exchanges' market-cap columns (`stock_quotes` reports rupees, BSE's table already reports crores), and treats BSE's always-NULL delivery percentage as *unknown* rather than *zero*.

### CLI scripts: rankers, value screens, and pattern scanners

Alongside the registry-driven screeners, `cli_scripts/` holds 23 standalone Python tools (~10,800 lines combined) that connect straight to Postgres, are read-only, and are designed to be run ad hoc as much as from the scheduler.

**`best_stocks.py` — the Elite 25 whole-universe ranker.** Every liquid NSE stock gets a 0–100 Elite Score across seven independent pillars: RS & Momentum (22 pts, IBD-style weighted 1/3/6/12-month return percentile), Trend & Stage (16 pts, a continuous version of the Minervini 50/150/200-DMA stack), Earnings Power (20 pts), Institutional (16 pts), Group & Sector (10 pts), Volume & Accumulation (8 pts), and Confluence (8 pts, how many other screeners/watchlists already agree). Two penalties subtract from the total — an extension penalty for trading too far above the 50-day average, and a volatility penalty based on ATR%. It supports `--explain SYMBOL` for a full pillar breakdown, `--asof` for point-in-time backtesting, and a `--max-per-sector` diversification cap.

**`undervalued_stocks.py` — a value screen with a trap filter.** Shares its universe and technical machinery directly with `best_stocks.py`. Scores a Value Score across six pillars — Cheapness (28 pts, the median of six valuation lenses, with earnings capped at 1.5× the 3-year average so a one-off asset sale can't fake a low P/E), Cheap-vs-what (14 pts, discount to peer and to the stock's own 5-year valuation range), Quality (20 pts, ROE/ROCE/ROA), Financial Strength (16 pts, a 9-point Piotroski F-score), Earnings Support (12 pts), and Catalyst (10 pts) — then subtracts up to **34 points of explicit value-trap penalties**: shrinking net income, rising leverage, thin interest cover, negative operating cash flow, a "falling knife" price structure, share dilution above 15%, promoter exit, and profit inflated by one-off items. Banks and NBFCs get three of the cheapness lenses and three of the trap checks turned off, since leverage and interest cover are the business model for a lender, not a distress signal. `--show-traps` prints "the list you are NOT buying" — names that look cheap but were flagged.

**`sector_rotation_analysis.py`** builds cap-weighted sector/subsector rotation entirely from raw OHLCV, splitting output into already-leading sectors, early/emerging rotation, and a drill-down into the top three sectors' leading subsectors and stocks — explicitly working around the fact that the historical `series` column on daily candles is NULL for most of the archive, so index-level confirmation isn't reliable and has to be reconstructed from constituent baskets instead.

**`msi_fundamental_alert_scanner.py`** runs six scan phases hourly, watching for MasterScore jumps/drops of 10+, EPS/Price Strength crossing 80, Buyer Demand upgrades into A-tier (with a reversion check so a stock that briefly dipped out of A-tier and back doesn't fire a false "upgrade"), new Blue Dot signals, FII increases, promoter buying, and new top-investor entries — deduplicated by a SHA-256 hash of each MSI row plus a 7-day cooldown per alert type.

**`earnings_alert_scanner.py`** watches for EPS surges — 100%+ YoY, 100%+ sequential, or a 75%+ multi-year annual trend confirmed by sales growth. The thresholds were tuned against the live database rather than guessed: a naive "100% growth" rule fires on 491 of 1,616 liquid names per quarter; adding quality gates (an EPS floor, a meaningful base, sales confirmation, a market-cap floor) cuts that to roughly 118.

**Other scanners**: `dormant_breakout_scanner.py` hunts coiled bases — tight range, muted 3-month return, no recent 52-week high, flattening moving averages, volume dry-up then an uptick. `vcp_tight_base_scanner.py` and `eod_breakout_scanner.py` detect and chart pattern setups with `mplfinance`, writing annotated PNGs to disk. `fundamentals_price_lag_scanner.py` finds stocks whose profit, revenue, and cash flow have risen for several straight fiscal years while the price has sat still for months — a fundamentals-ahead-of-price screen.

**Infrastructure scripts**: `calculate_sector_scores.py`/`calculate_subsector_scores.py` compute the daily composite scores (35% MasterScore, 35% momentum, 30% quality) behind the Sector and Subsector dashboards. `run_screeners.py` upserts the momentum/earnings scores nightly. `tune_radar.py` is a self-honesty harness for Breakout Radar (see below) — it measures real recall and precision against a random-universe baseline, and its finding that the earliest "Armed" stage carries roughly zero edge over random selection is *why* the corresponding live-watch job ships disabled by default. `sync_schema_skills.py` introspects the live database's schema and diffs it against the project's own hand-maintained schema documentation, so drift between the two is a detectable, fixable event instead of silent rot.

**Options and broker CLIs**: `backtest_0dte_iron_butterfly.py` backtests a NIFTY expiry-day strategy (sell the ATM straddle, buy 1% OTM wings, exit in the last 20 minutes to harvest theta decay). `fyers_option_buying_interest.py` is a live options scanner over the Fyers websocket that ranks every call/put on volume velocity, bid/ask imbalance, and OI buildup, surfacing a single best candidate rather than a flood of signals. `fyers_index_options_agent.py` layers a GPT tool-calling agent on top of that (more on this below). `kite_holdings_positions.py` is a parallel Zerodha Kite Connect wrapper for portfolio/holdings/positions.

### Live Scanner: six real-time market feeds

`GET /api/v1/scanner/*` serves six intraday/EOD feeds over one shared SQL-builder contract (`src/lib/scanner/queries.py`):

- **Volume Spurts** — NSE and BSE volume gainers merged so a stock surging on either exchange shows once, tagged which exchange(s), with a computed surge multiplier against its 2-week average.
- **Price Band Hitters** — circuit-limit hits from both exchanges. The BSE side alone gets a penny-stock filter (a ₹10 minimum price, a ₹0.25 Cr minimum traded value) that cuts a typical session's ~550 raw BSE circuit hits down to about 65 names with real money behind them.
- **52-Week High/Low** — new extremes with breakout percentage, streak length, and whether the breakout held or faded intraday.
- **Most Active** — ranked by absolute rupee turnover, a deliberately different signal from Volume Spurts' relative-surge measure.
- **OI Spurts** — F&O open-interest buildups per contract, decoded into Long Buildup / Short Buildup / Short Covering / Long Unwinding.
- **Delivery Spikes** — rewritten after an earlier version silently returned zero rows whenever a session's delivery data hadn't landed yet; now compares today's delivery against a 20-session baseline and classifies Accumulation / Distribution / Absorption.

Every feed takes an optional `?date=`, and rather than trusting `MAX(date)` on the whole table (which goes empty the instant one feed hasn't landed for the day), each one resolves backward to the latest session that actually has data *for that specific feed*, reporting the served date, the requested date, and whether they match — so the frontend can say "showing Friday's data" instead of silently substituting. A shared confluence pass tags every row with which *other* scanners also flagged that symbol the same session. Several query rewrites are documented inline with before/after numbers: sargable date ranges instead of `timestamp::date = x` turned a 5.1-million-row scan into a 60ms index seek; a materialized CTE hint on a BSE join cut 6.9 seconds to 88ms; rewriting a correlated `NOT EXISTS` ETF filter as an uncorrelated `NOT IN` cut 75.7 seconds to 28.8ms.

### Watchlists: CRUD, a decision board, and a digest

The core watchlist API (`/api/v1/watchlists`) handles create/rename/delete, adding and removing symbols (resolved to ISIN via the equity bridge table), and per-symbol notes. The recently-added sorted view enriches every symbol with live MSI scores (MasterScore, EPS/Price Strength, Group Rank, Buyer Demand) before sorting, so any MSI-derived field is just as valid a sort key as a raw watchlist column — nulls always sort to the bottom regardless of direction.

A second "decision board" layer, mounted on the same URL prefix, adds bulk paste-many add/remove (splitting on newline, comma, tab, or space), copy/move between lists, per-symbol trade-plan metadata (notes, tags, target, stop, conviction), list duplication, CSV export, and a "push to Fyers" sync that writes the list straight into the broker's own watchlist.

The **Watchlist Digest** (`src/lib/watchlist_digest.py`) answers "what changed since I last looked" without a snapshot table — everything it diffs is already date-keyed, so a missed cron job never leaves a gap. It compares price/volume structure, MSI score deltas, Breakout Radar stage transitions, convergence-tier movement, and the full corporate tape (insider filings, block/bulk deals, board meetings) between now and N days ago, turns every difference into a weighted "highlight" (a new 52-week high is worth more than a small price move), and sums those into a change score that ranks the whole digest — with the explicit design note that a name nine different screeners flagged over nine separate days is one piece of information, not nine.

### Alerts: seventeen triggers and a convergence engine

`src/lib/alerts/triggers.py` runs 17 distinct triggers on a schedule — block-deal entries, short squeezes, FII/MF clustering, VCP tightness, episodic pivots, quality consolidations and pullbacks, insider buying clusters, bullish OI buildups on high-MSI names, fundamentals-confirmed circuit breakers, pivot proximity, MSI portfolio adds, superstar-investor clusters, and four pipeline-driven triggers (new Track A entries, Track B breakouts, sector rotation, conviction spikes) — plus 13 more MSI-change triggers covering star-investor entries/exits, score surges, buyer-demand upgrades, group-rank improvement, blue-dot appearances, EPS acceleration, and promoter or revenue surges. New alerts are deduplicated against the day's existing rows and routed — every high-severity alert goes to a dedicated Telegram channel individually, followed by a rollup message linking to that day's web report.

On top of the raw alert stream sits a **convergence-tier engine** that groups screeners into four independence pillars (fundamental, technical, institutional, momentum) so three RS-derived screeners agreeing counts as one piece of evidence, not three — and weights each screener by how rare its hits were *that specific day*, since a screener printing 1,900 names on a given session is weak evidence and one printing 7 is strong. Without that adjustment, the raw tier system was — per its own in-code admission — about 75% noise. A separate "Golden Rule" requires four independent legs (RS leadership, momentum trigger, institutional flow, insider conviction) to fire simultaneously alongside MSI ≥80, reported per-leg so a near-miss shows as "4 of 5" instead of a silent false.

Six dedicated Telegram channels carry different alert types (daily report, stock alerts, general, watchlist, MSI-fundamental, paper-trading), plus a separate channel wired directly to the global exception handler. Alerts can carry user-uploaded attachments — images, audio, and auto-compressed video, size-limited by type — added through the Chrome extension's price-alert dialog and stored under UUID-named folders.

### Fundamentals and MSI data

Screener.in-sourced tables exist in the schema but are empty; `msi_fundamental_financial_lines` (MarketSmith India data) is the real valuation source used everywhere. An MSI enrichment layer keeps an in-process map of every symbol's current MasterScore, EPS/Price Strength, Group Rank, and Buyer Demand, refreshed every 5 minutes during market hours and warmed on server startup so the very first request after a restart isn't slow. Dedicated endpoints serve pivoted financial statements (income, ratios, balance sheet, cash flow) with line-item alias resolution so "Net Profit," "Profit After Tax," and "PAT" all map to the same field; MSI's plain-English score explanations; pass/fail investment checklists; and a browsable surface of MSI's own idea-list folders, industry groups, market indices, "Stocks to Watch," the Blue Dot list, and Top Investors.

### The agentic AI research layer

This is the platform's most substantial rewrite story. An earlier version used a CrewAI-style tool-calling agent that burned iterations hunting for data and — worse — five of its six retrieval tools referenced columns that don't actually exist in the schema, so early reports were written on almost nothing. The replacement throws out free-form tool use entirely in favor of a deterministic pipeline:

1. **A datapack** (`src/lib/research/datapack.py`) fetches everything verifiable about a symbol — identity, price/technicals, MSI fundamentals, quarterly-earnings trend, shareholding, corporate events (with an explicit guard for splits and bonuses, which would otherwise make an unadjusted price series lie), and every screener's hits — in parallel, each block independently fault-tolerant.
2. **A pipeline** runs three analyst passes in parallel on a cheap model (fundamental, technical, flow/news), each returning strict JSON, then a synthesis pass on a stronger model reconciles them into a full report: headline, stance, a conviction score explicitly capped at 3 out of 5 when data coverage is thin or the analysts disagree, and a thesis that must carry a horizon, a target price, and an invalidation price anchored to a real technical level rather than a round percentage.
3. **Provenance is enforced, not assumed.** Every numeric claim must cite whether it came from the database, the web, or inference — and if from the database, the exact field path. The model is handed an explicit map of every citable path rather than a description of the convention, because the first live run fabricated two citations by guessing at a shape it could only infer.
4. **A verification pass** independently walks every cited path and checks the model's quoted number against the real value in the datapack (tolerant of rounding), flagging fabrication and transcription errors — "this doesn't make the reasoning correct, it only guarantees the arithmetic is traceable."
5. **Self-grading.** Because every thesis carries a horizon and an invalidation price, a scoring pass later replays the actual candle history to determine, deterministically, whether the target or the invalidation was hit first — and tracks maximum adverse excursion, on the reasoning that a thesis which ended flat after being 18% underwater "was not roughly right, it was a position nobody could have held."

Reports run as background jobs at three depths (quick/standard/deep) with live progress polling, and a follow-up Q&A endpoint answers strictly from a report's own frozen datapack rather than fresh data, so a newer number can't make an old answer look inconsistent.

Two smaller GPT integrations sit elsewhere in the codebase: a lighter overlay inside the autonomous paper-trading bot validates the day's market regime and individual trade candidates (falling back to a pure-quant decision if no API key is configured), and a genuinely tool-calling agent behind the Fyers options scanner is explicitly hard-coded to never place a broker order — its only tools are news search and read-only market-data lookups, rate-limited to 20 calls an hour, and it returns a structured buy/wait/avoid recommendation with a strike, an invalidation level, and cited sources.

### Breakout Radar: the one stateful screener

Every screener elsewhere in the platform is stateless — it recomputes a fresh list every evening with no memory of what a stock looked like yesterday. Breakout Radar is the deliberate exception: a nightly job assigns every symbol one of five stages (Ignore → Accumulating → Armed → Triggered → Extended) and persists it, so the system can detect the transition itself — a stock just becoming "Armed" is the single most useful event the whole subsystem emits. An intraday live-watch job can subscribe to the day's armed list over the Fyers websocket for real-time pivot crosses, but it ships **off by default**, because the tuning harness (`tune_radar.py`) measured that the Armed stage alone carries roughly zero edge over a random selection from the same universe — an honest negative result the project chose not to hide behind a feature flag that defaults to "on."

### Institutional Pipeline, autonomous paper trading, and the rest

A parallel institutional-style screening pipeline runs two independent tracks nightly: **Track A** ("Sector Momentum") filters to stocks in the top third of their industry group by MSI rank before layering on fundamental and technical readiness — higher win rate, moderate upside. **Track B** ("Early Catch") deliberately ignores industry rank and instead hunts early accumulation signals — rising delivery percentage, block-deal upticks, forming base patterns — lower win rate but, per its own framing, occasional 5–10x winners. An F&O mode intersects both tracks against the options-active universe.

Two simulated bots run a full daily cycle on their own: a Swing Equity bot (₹2 lakh notional capital, VCP/consolidation breakouts on high-MSI names) and an F&O Options bot (₹5 lakh notional, four spread strategies), each running market-regime detection, entries, and portfolio stats, optionally validated by the GPT overlay described above, with a separate midday pass that only manages trailing stops and DTE exits — no new entries outside the main cycle.

Rounding out the backend: a **chart generation service** renders `mplfinance` candlestick PNGs with configurable per-timeframe moving averages, cached to disk and reused within the same period; an **F&O Desk** service layer serves the option chain, chain history, per-contract intraday candles, OI positioning, and futures basis/rollover, normalizing a documented Groww data quirk where historical strike prices were stored as raw values and later ones as ×100-scaled integers; an **institutional flow and Smart Money conviction engine** scores every institution on the block/bulk-deal tape by the ratio of net-to-gross traded value, so a desk doing ₹8,000 Cr of gross volume with near-zero net exposure gets correctly labeled a market maker rather than mistaken for conviction buying; a **corporate-events layer** tracks insider filings (explicitly excluding ESOP allotments and pledges as "not conviction trades"), block/bulk deals, and board meetings; a **Cockpit aggregation layer** composes all of the above into cheap, independently cached slices for the dashboard's home terminal; **Market Map and heatmap services** pre-build treemap JSON to a dated on-disk cache after each close rather than computing it per request; a **trade journal API** handles manually entered buy/sell fills with FIFO-style position math and live portfolio risk; and **sector, subsector, and peer-browsing** endpoints rank any group's constituents around an anchor symbol for the frontend's sequential "Symbol 360" navigation.

### The scheduler: what runs on its own

An in-process APScheduler drives everything time-based, every job dispatched to its own thread so a slow run can't block the API. The full nightly/intraday rhythm (IST):

| Time | Job |
|---|---|
| 05:00 | Rebuild the F&O metadata cache |
| Hourly, 08:00–20:00 | MSI fundamental alert scan |
| 09:00 | Pre-market Telegram brief |
| 09:10 | Radar live-watch (off by default) |
| Every 30 min, 09:30–15:30 | Intraday alert evaluation |
| 13:00 | Intraday position check (exits only, no new entries) |
| Hourly, 14:00–18:00 | Convergence-tier recompute |
| 15:35 | Radar EOD summary (off by default) |
| 16:30 | EOD alert evaluation |
| 16:30 | Sector scores |
| 16:35 | Subsector scores |
| 17:00 | Signal Lab: all 14 screeners |
| 17:15 | Momentum/earnings screeners |
| 17:15 | Institutional pipeline full scan |
| 17:30 | Autonomous paper-trading daily cycle |
| 17:45 | Breakout Radar nightly staging |
| 17:50 | Dashboard rankings (Best/Worst) |
| 17:50 | Heatmap disk cache rebuild |
| 00:30 | Earnings surge scan (runs daily, including weekends, since results and filings land then too) |

Outside the Python process, a `poll-deploy.sh` script runs every minute via cron, pulling and restarting the service whenever `main` advances — a lightweight continuous-deployment loop without a CI/CD platform in front of it.

### Schema documentation as a maintained artifact

Rather than a migrations framework, tradepy documents its own schema by hand across eleven files (equity master, market data, options, fundamentals, corporate events, and so on), and keeps that documentation honest with a script that introspects the live database and diffs it against what's written down — so drift between the two is something the project can detect and fix, not something that silently accumulates.

---

## The dashboard: trading-client-web

### Two design systems, one philosophy

The frontend runs two named design systems switched by a theme toggle — "Quant Edge" (near-black surfaces, an ice-blue primary) for dark mode, and "Tactical Precision" (an off-white "Swiss Atelier" look, deep blue primary) for light — both defined as CSS custom properties and re-exposed as Tailwind v4 tokens, including a validated categorical data-viz palette and a five-tier "Diamond → Bronze" convergence color ramp checked for contrast in both themes. The stated philosophy is **Instrument Grade UI**: high information density, no unnecessary whitespace, visible in the near-universal use of 9–11px type and tight padding across the app's tables. Panel boundaries are drawn with background-color shifts rather than borders wherever the "No-Line Rule" is followed. Manrope carries headlines and large values; Inter carries every data table and body of text.

### Getting around: the mega menu and the command palette

A five-category mega menu — **Discover**, **Analyze**, **Flow**, **Portfolio**, **Systems** — organizes 26 of the app's 38 routes around a "what am I trying to do" framing rather than a flat page list. A command palette (Ctrl/Cmd+K) searches four namespaces at once — pages, live symbol search, watchlists, and screeners — with a custom fuzzy scorer that favors exact and prefix matches over scattered ones, and promotes ticker-looking queries straight to symbol results.

### Discover: what should I be looking at today

- **Breakout Radar** — five tabs (Armed / Newly Armed / Triggered / Accumulating / Do Not Chase) with box quality, consolidation days, buy-above price, stop, and risk:reward per setup, plus a sector-concentration warning when the top setups cluster too heavily.
- **Live Scanner** — all six backend feeds behind one UI: a session date-picker that resolves backward the same way the API does, a market-breadth strip, per-scanner sub-filters, and server-side sortable, infinite-scrolling tables.
- **Convergence Tracker** — the four-pillar confluence view, with a Diamond-to-Bronze tier system, a "Golden Rule" badge, spotlight cards for the top candidates, and conviction meters that break down exactly which legs are firing.
- **Ideas List (MSI filters)** — the largest single page in the app: a collapsible folder tree of MarketSmith's own screen categories, plus dedicated views for the 197 industry groups, key indices, Stocks to Watch, the Blue Dot list, and a searchable Top Indian Investors table.
- **Earnings Power / Technical Momentum** — the pre-computed momentum and earnings screeners, with per-type score-breakdown columns and sector/F&O/min-score filters.
- **MSI Daily Report** — the day's MSI change feed grouped by alert type, plus three analytics tabs answering "which alerts actually pay" (a forward-return chart per alert type against an all-alerts baseline), alert-flow trends over time, and a "repeat flags" table of names the feed keeps re-flagging.

### Analyze: is this specific name any good

- **Symbol 360** — the single-symbol deep-dive terminal, reachable from virtually every table in the app: a sticky quote strip with a labeled 52-week-range marker, a candlestick chart with moving averages, an MSI score card with a circular Master Score ring, quarterly earnings with revision arrows, a per-checklist pass/fail breakdown, an industry-peer ranking rail, ownership and insider panels, and a full-width "Tactical Intelligence" strip showing every currently-firing screener's reasoning for that symbol. Only the eagerly-needed sections load immediately; everything else loads lazily as it scrolls into view, cutting a symbol open from eleven requests to three.
- **Tactical Cockpit (Terminal)** — the personalized home base: a session-phase pill, a market strip, an open-positions panel pulled from the journal, an "attention" panel of watchlist names needing action, a collapsible leaders/laggards dashboard across market-cap tiers, and three "found for you" panels surfacing fresh Convergence, Radar, and 52-week-high hits.
- **AI Stock Research** — starts an async research job at three depth tiers, polls it to completion, and renders the finished report with a stance/conviction header, an annotated price chart showing entry/target/invalidation, a verification bar showing what percentage of the report's claims were confirmed against the database, bull/bear cases, risks with mitigants, and a follow-up Q&A box scoped to that report's frozen data.
- **Fundamental Comparison** — a side-by-side two-point-in-time snapshot for one symbol, anchored either to two explicit dates or to a specific Fyers alert.
- **Industry / Sector / Subsector rankings** — rotation state (leading, improving, weakening, lagging), weekly movers, and a "constituent breadth" metric — the percentage of a group's *own* stocks above their 50-day average — specifically to show that a group's strength isn't being carried by two heavyweight names.

### Flow: where is the money going

- **Smart Money** — six tabs covering multi-buyer accumulation campaigns, institutions ranked by conviction rather than raw volume, audited ownership changes, insider activity, sector deal flow, and a five-pillar composite score.
- **Insider Hub** — net insider buying ranked by conviction, cluster detection (several insiders buying inside a configurable window), and a "what pays" tab that splits forward returns by buyer category — explicitly noting that Management buying has historically outperformed Promoter buying in this dataset.
- **Institutional Flow** — FII/MF holding deltas, block deals, and bulk deals with a leaderboard and a configurable lookback window.
- **F&O Desk** — an option-chain workbench with an OI profile chart, a click-to-load intraday candlestick per contract, and an ATM-centered calls/puts ladder, alongside OI positioning, a futures basis/rollover desk, and market-wide flow.
- **Option Charts (legacy)** — the earlier cascading symbol → year → expiry → strike charting tool, kept running side-by-side with the newer F&O Desk rather than removed.
- **Market Map** — a hand-rolled DOM treemap (not SVG, so labels render with real fonts and every cell stays keyboard-reachable), sized by market cap or turnover and colored by move or Master Score, with linked breadth, rotation, and index views and full keyboard navigation (search-to-highlight, fullscreen toggle).
- **Events Calendar** — a corporate-action calendar auto-classified from free-text purpose strings into dividends, splits, bonuses, results, and board meetings.

### Portfolio: what am I in and what needs me

- **Watchlist** — a "decision board" with three interchangeable views (card board, dense table, heatmap), a ten-option custom sort dropdown mixing raw and MSI-derived fields, bulk multi-select operations, CSV export, a Fyers sync button, and a symbol drawer with a live risk/reward calculator for editing a name's trade plan.
- **Watchlist Digest** — the diff view described on the backend side, surfaced with a summary strip, a sector-performance chart, and expandable per-symbol change cards.
- **Trade Journal** — positions, closed-trade history, performance stats broken out by setup/sector/conviction, and a risk panel showing total exposure and what happens if every stop fills at once. A buy form computes position risk live as the user types.
- **Fyers Alerts** — a sortable, auto-refreshing table of live broker price alerts with a detail dialog for editing notes and attaching media.
- **Telegram Alerts** — the raw signal feed grouped by symbol, with a confluence-intensity bar and a dedicated "wash trade" tab that pairs matching buy/sell alerts from the same client to show realized P&L on scalp trades.

### Systems: what runs on its own, and is it working

- **Signal Lab** — see the registry-driven mechanism below.
- **Screener Attribution (Cohorts)** — a cross-screener leaderboard by average/median/win-rate/excess-return, with a per-screener detail view showing whether the edge decays over time, whether the screener's own internal score actually ranks anything, and whether the average return is being propped up by one good quarter.
- **Daily Reports archive** — a calendar of every past report, a track record of how each report's own picks performed, a "persistence" view of which screeners keep returning to the same names, and a symbol-trace view showing every report a given stock ever appeared in.
- **Pipeline Dashboard** — the Track A / Track B / F&O-mode institutional pipeline, each its own sortable, exportable table, with a live market-health bar and a progress-tracked "Full Scan" trigger.
- **Algo Cockpit** — backtests the same strategies the paper-trading bots run live, with win rate, profit factor, and a full reversible trade log.
- **Paper Trading** — the live dashboard for the two autonomous bots: per-bot enable/disable, combined P&L and win-rate cards, and active/history trade views.

### Two more things worth naming

A pair of long-form educational guide pages — a full CAN SLIM® playbook and a MarketSmith India tool guide — render through one shared article template with scroll-spy navigation, sourced entirely from static content files with no per-guide component code. A global **Settings** page lets the user configure default chart timeframe and, per timeframe, up to four moving-average studies with a live debounced preview rendered from the same server-side chart pipeline Symbol 360 uses.

### The registry-driven Signal Lab UI

This is the frontend half of the mechanism described on the backend: `SignalLab.jsx` fetches the whole screener registry once, groups known screener IDs into four cosmetic categories purely for layout (any unrecognized ID falls into an auto-generated "Other Scanners" section rather than disappearing), and renders every screener's criteria chips, result columns, and score breakdown directly from that metadata. A generic `ScreenerTable` builds its headers from whatever `columns` the registry supplies and formats each cell through a typed value renderer; a generic `DetailGrid` shows whatever fields a given row happens to carry and silently skips whatever it doesn't. The practical result: shipping a fourteenth or fifteenth screener on the backend has never required a frontend deploy.

### Real-time, charting, and the rest

Three refresh patterns cover the whole app — session-gated polling that only runs while the Indian market is actually open (checked client-side against IST), fixed-interval polling regardless of session for a few pages that need it (price alerts every 30 seconds, an active pipeline scan every 3 seconds), and one genuine Server-Sent Events channel that pushes Signal Lab run-status toasts app-wide. A shared request-caching layer de-duplicates in-flight GETs and short-TTL-caches responses so overlapping polls across sibling panels collapse into a single network call.

Charting runs on TradingView's open-source `lightweight-charts` library for every candlestick view (with a secondary path through TradingView's own hosted `tv.js` widget as an alternative), and Recharts for every statistical chart — bar, area, and the custom-cell treemaps used for sector and industry heatmaps.

Cross-cutting conveniences worth naming: most pages sync their tab/filter/date state into the URL so views survive a reload and are shareable; keyboard shortcuts cover the command palette, symbol search, chart zoom reset, Market Map fullscreen, and prev/next navigation through Symbol 360's queue; and the AI Stock Research feature is the app's one LLM-backed page, explicitly designed around the source-verification pass described on the backend rather than presenting model output as fact.

---

## The broker overlay: trading-client-chrome-ext

### What it actually is

The Chrome extension is a Manifest V3 build that layers the platform's intelligence directly onto Fyers' web trading terminal. It doesn't authenticate to Fyers itself — it passively reads the session cookie Fyers' own login already set, relays that as a bearer token to tradepy, and keeps it in sync using `chrome.cookies.onChanged` plus a one-minute `chrome.alarms` heartbeat (chosen specifically because MV3 service workers are torn down after roughly 30 seconds idle, and a plain `setInterval` doesn't survive that). It is read-only intelligence and alert management — the only two things it ever writes back to Fyers are watchlist membership and price-alert creation, and even alert creation is routed through tradepy rather than calling Fyers directly, so tradepy can attach its own metadata to the alert.

### The real cockpit lives in the side panel

Clicking the toolbar icon opens Chrome's side panel, not a popup — a persistent trading-intelligence dock with three tabs:

- **Fundamentals** (default) — a header card with sector/industry chips and an earnings-due-date badge color-coded by urgency, a circular Master Score ring, a one-click watchlist toggle that auto-selects the correct Fyers watchlist shelf (F&O / Large / Mid / Small Cap) based on the stock's own classification, a compact EPS/Price/Buyer-Demand/Group-Rank grid, a seven-year annual statement view, a top-investors list, an interactive ownership-pattern bar chart, and the company's MSI-sourced description.
- **Settings** — currently one toggle: automatically bypass MarketSmith India's login screen by injecting a premium session token (see below).
- **Alerts** — fully built (per-alert cards showing trigger direction and a technical-distance grid) but, as of this scan, not reachable from the panel's own navigation bar — a real, verifiable piece of work-in-progress functionality rather than a claimed feature.

A lightweight content script tracks whatever symbol is currently on-screen by watching the broker's own TradingView-powered chart widget for DOM mutations, and broadcasts every change to the side panel so it always reflects the chart the user is actually looking at — no polling, no manual symbol entry.

### The price-alert hijack

Creating a price alert on Fyers' own platform gets intercepted before it ever reaches Fyers' servers: a page-context script monkey-patches `window.fetch`, catches the outgoing alert request, and pauses it while a custom dialog — injected as an iframe directly into the broker's page — collects an alert name, a value, private internal notes (explicitly *not* sent to Fyers), and optional image/audio/video attachments. Attachments are base64-encoded to cross the extension messaging boundary, then the whole thing is submitted through tradepy rather than Fyers, so the extra metadata can be persisted server-side; Fyers' own paused request is then resolved with a fabricated success response so its native UI never knows the difference.

### What's built but switched off

A few features exist in the codebase but aren't currently live, which is worth noting honestly rather than glossing over: a draggable, resizable on-page overlay version of the same cockpit (an alternative to the side panel) is fully implemented but gated behind a hardcoded flag; the Alerts tab described above has no way to open it from the current navigation; and a "Signal Lab Intelligence" panel is fetched on every fundamentals load but its render block is commented out of the template. None of these affect what currently ships — they're the visible trail of a project still being actively shaped.

---

## Closing thoughts

Taken together, the three repositories form one coherent system built by one person: a scoring and screening brain that never trusts a naive threshold without empirically checking how much noise it produces, a dashboard dense enough to answer "what should I be looking at" and "what am I holding" without leaving the page, and a broker overlay that puts the same intelligence directly where trades actually get placed — plus, running alongside all of it, an AI research layer built specifically to distrust its own output until every number in it can be traced back to a real row in the database.
