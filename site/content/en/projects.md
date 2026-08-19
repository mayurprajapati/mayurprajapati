---
title: "Projects"
type: "homepage"
description: "Selected engineering projects — WebSocket TCP tunneling, a Jenkins Groovy shared library at 1,200+ jobs, and an end-to-end trading/market-intelligence stack."
intro: >-
  A closer look at the platforms and systems behind the résumé bullets — what they do, how they're built, and what changed because of them.

projects:
  - title: "Trading Platform"
    flagship: true
    tagline: "Personal project — end-to-end market-intelligence system"
    icon: "chart-line"
    tech: ["Java", "Hibernate", "Flask", "gRPC", "PostgreSQL / TimescaleDB", "React", "LLM / Agentic AI"]
    description: >-
      A full market-intelligence stack built solo, end to end: a Java/Hibernate ingestion engine that scrapes and normalizes market data, a Flask REST API, a gRPC bridge connecting the Java and Python sides, pandas-based scoring pipelines, an agentic-AI research layer, and a React dashboard with a Chrome-extension broker overlay for live trading context.
    highlights:
      - "Columnar compression on a 152M-row OHLC candle table cut a hot query from 27s to 0.8s (~27x) — segment/order-by tuning and chunk sizing on TimescaleDB."
      - "gRPC bridge lets the Java scraping/ingestion engine and the Python (Flask + pandas) scoring layer stay in their best-fit languages instead of one compromising for the other."
      - "Agentic-AI research layer automates report generation and market analysis on top of the scored data."
    blog_post: "timescaledb-compression-152m-row-query"

  - title: "Briq WebDriver"
    tagline: "Java · WebSockets · TCP Tunneling"
    icon: "network-wired"
    tech: ["Java", "WebSockets", "TCP Tunneling", "FFmpeg"]
    description: >-
      Secure remote execution and live debugging over WebSocket TCP tunnels. Removes the need for local tool installs, keeps client source code protected, and powers FFmpeg-based video evidence capture during automated runs.
    highlights:
      - "A public WebSocket server bridges a proxy HTTP server and a proxy HTTP client — no VPN, no exposed ports on the client machine."
      - "Used in production to run Selenium sessions and capture video evidence without installing tooling on client infrastructure."
    blog_post: "efficient-tcp-tunneling-using-websockets"

  - title: "Jenkins Shared Library"
    tagline: "Groovy · Jenkins · CI/CD"
    icon: "cogs"
    tech: ["Groovy", "Jenkins", "GitLab CI/CD", "Cross-platform (Unix/Windows)"]
    description: >-
      Reusable, versioned pipeline components — build, test, deploy — shared across 1,200+ Jenkins jobs. The single entry point for bot lifecycle management, Slack alerting, and credential obfuscation across GitLab CI/CD.
    highlights:
      - "Standardizes cross-platform (Unix/Windows) pipeline execution across every job that consumes the library."
      - "Centralizes credential handling and DR validation before any production promotion."
---
