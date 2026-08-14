---
title: "Efficient TCP Tunneling Using WebSockets: A Step-by-Step Guide"
date: 2023-04-21
draft: false
description: "Tunnel HTTP traffic over WebSockets with a bridge server and two proxy endpoints — for VPN-restricted services, Selenium from a client machine, or hiding your public IP."
tags: ["websocket", "java", "proxy", "https", "selenium"]
featured_image: "/images/blog/websocket-tcp-tunneling.png"
og_image: "/images/blog/websocket-tcp-tunneling.png"
external_url: "https://medium.com/@mayurprajapatiin/efficiently-transfer-http-traffic-using-websockets-a-step-by-step-guide-3f2991b591f7"
external_source: "Medium"
---

![WebSocket-based TCP tunneling architecture](/images/blog/websocket-tcp-tunneling.png)

*Architecture diagram from the original Medium post — a public WebSocket server bridges a proxy HTTP server and a proxy HTTP client.*

Some services are only reachable from a specific machine — behind a VPN, inside
a client's network, or only from the system where your Selenium tests run. This
guide shows how to move HTTP traffic across that boundary by tunneling it
through WebSockets.

The full post covers the architecture and the complete message flow: a public
WebSocket server bridges a Proxy HTTP Server and a Proxy HTTP Client, which wrap
HTTP requests and responses in WebSocket messages — including metadata messages
for payload size, and the synchronization needed to keep the asynchronous
WebSocket flow sequential like HTTP itself.

[**Read the full post on Medium →**](https://medium.com/@mayurprajapatiin/efficiently-transfer-http-traffic-using-websockets-a-step-by-step-guide-3f2991b591f7)
