---
title: "How TimescaleDB Compression Cut a 152M-Row Query from 27s to 0.8s"
date: 2026-08-10
draft: false
description: "Columnar compression on a 152-million-row OHLC candle table took a time-series query from 27s to 0.8s — segmentby/orderby choices, chunk sizing, and the numbers behind the 27x speedup."
tags: ["postgresql", "timescaledb", "sql", "performance"]
featured_image: "/images/blog/timescaledb-compression.jpg"
og_image: "/images/blog/timescaledb-compression.jpg"
external_url: "https://medium.com/@mayurengineer/how-timescaledb-compression-cut-a-152m-row-query-from-27s-to-0-8s-e1b25242f0da"
external_source: "Medium"
---

![Illuminated car tachometer](/images/blog/timescaledb-compression.jpg)

*Photo by [Chris Liverani](https://unsplash.com/@chrisliverani) on [Unsplash](https://unsplash.com/)*

A 152-million-row table of OHLC candles, a query that took **27 seconds**, and a fix that
brought it down to **0.8 seconds** — using TimescaleDB's columnar compression rather than
more indexes or more hardware.

The full post covers how the hypertable was chunked, how `segmentby` and `orderby` were
chosen for the access pattern, and what the before/after `EXPLAIN ANALYZE` plans actually
show.

[**Read the full post on Medium →**](https://medium.com/@mayurengineer/how-timescaledb-compression-cut-a-152m-row-query-from-27s-to-0-8s-e1b25242f0da)
