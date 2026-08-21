---
title: "Projects"
type: "homepage"
description: "Selected automation projects — a Reflection-based test-execution engine replacing JUnit across 1,200+ modules, WebSocket remote test execution, and a Jenkins shared library orchestrating 1,200+ jobs."
intro: >-
  A closer look at the automation platforms behind the résumé bullets — what they test, how they're built, and what changed because of them.

projects:
  - title: "BriqBotRunner"
    flagship: true
    tagline: "Centralized test-execution engine — replaced JUnit across 1,200+ modules"
    icon: "vial"
    tech: ["Java", "Reflection", "Maven", "Test Execution", "Jenkins"]
    description: >-
      An in-house test-execution engine built to replace JUnit across the entire automation estate. Dynamic class/method dispatch via Java Reflection gives one entrypoint for running any suite on any platform — with consistent reporting and no per-module runner boilerplate.
    highlights:
      - "Zero-downtime migration of 1,200+ automation scripts off JUnit, cutting compile overhead and simplifying maintenance across the framework."
      - "One runner for Web (Selenium, Playwright), Desktop (Appium, WinAppDriver), API (RestAssured), and OCR/PDF test surfaces."
      - "Drives 350+ production bots from a single, versioned execution contract."

  - title: "Briq WebDriver"
    tagline: "Remote test execution & debugging over WebSocket TCP tunnels"
    icon: "network-wired"
    tech: ["Java", "WebSockets", "TCP Tunneling", "Selenium", "FFmpeg"]
    description: >-
      Secure remote test execution and live debugging over WebSocket TCP tunnels. Runs Selenium sessions on client infrastructure with no local tool installs, keeps client source code protected, and powers FFmpeg-based video evidence capture for every run.
    highlights:
      - "A public WebSocket server bridges a proxy HTTP server and a proxy HTTP client — no VPN, no exposed ports on the client machine."
      - "Used in production to run Selenium sessions and capture video evidence without installing tooling on client infrastructure."
    blog_post: "efficient-tcp-tunneling-using-websockets"

  - title: "Jenkins Shared Library"
    tagline: "Groovy · Test orchestration across 1,200+ jobs"
    icon: "cogs"
    tech: ["Groovy", "Jenkins", "GitLab CI/CD", "Cross-platform (Unix/Windows)"]
    description: >-
      Reusable, versioned pipeline components — build, test, deploy — shared across 1,200+ Jenkins jobs. The single entry point for test-run lifecycle management, failure recognition, Slack alerting, and credential obfuscation across GitLab CI/CD.
    highlights:
      - "Standardizes cross-platform (Unix/Windows) test execution across every job that consumes the library."
      - "Centralizes credential handling and DR validation before any production promotion."

  - title: "Trading Platform"
    tagline: "Personal project — end-to-end market-intelligence system"
    icon: "chart-line"
    tech: ["Java", "Hibernate", "Flask", "gRPC", "PostgreSQL / TimescaleDB", "React", "LLM / Agentic AI"]
    description: >-
      A full market-intelligence stack built solo, end to end: a Java/Hibernate ingestion engine that scrapes and normalizes market data, a Flask REST API, a gRPC bridge connecting the Java and Python sides, pandas-based scoring pipelines, an agentic-AI research layer, and a React dashboard with a Chrome-extension broker overlay.
    highlights:
      - "Columnar compression on a 152M-row OHLC candle table cut a hot query from 27s to 0.8s (~27x) — segment/order-by tuning and chunk sizing on TimescaleDB."
      - "gRPC bridge lets the Java scraping/ingestion engine and the Python (Flask + pandas) scoring layer stay in their best-fit languages instead of one compromising for the other."
      - "Agentic-AI research layer automates report generation and market analysis on top of the scored data."
    blog_post: "timescaledb-compression-152m-row-query"
---
