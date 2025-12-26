# Site Tomograph 網站斷層掃描

[![License: AGPL-3.0](https://img.shields.io/badge/License-AGPL--3.0-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688.svg)](https://fastapi.tiangolo.com/)
[![Three.js](https://img.shields.io/badge/Three.js-r158-000000.svg)](https://threejs.org/)
[![3d-force-graph](https://img.shields.io/badge/3d--force--graph-1.73-FF6B6B.svg)](https://github.com/vasturiano/3d-force-graph)
[![Tests](https://img.shields.io/badge/Tests-48%20passed-22c55e.svg)](tests/)

[← Back to Muripo HQ](https://tznthou.github.io/muripo-hq/) | [中文](README.md)

A low-light, high-immersion 3D website structure diagnostic tool. Enter a URL and watch the site topology grow in real-time from the center, intuitively discovering dead links, slow pages, and orphan nodes through visualized "decay mechanisms."

![Site Tomograph](assets/preview.webp)

> **"This isn't just a visual piece—it's a professional diagnostic instrument that lets developers 'see' website link structure."**

---

## Core Concept

Traditional website health check tools give you a cold report. This tool lets you **witness** how a website's neural network grows and where it starts to decay.

Through low-light, high-immersion 3D visualization, we've created a space where developers can quietly and comfortably observe the growth and decay of website structures.

---

## Features

| Feature | Description |
|---------|-------------|
| **Real-time Topology Growth** | After entering a URL, watch the site structure asynchronously expand outward from the center |
| **Latency Heat Mapping** | Intuitively display page response delays through particle flow speed on connections |
| **Dead Link Tracking** | Click any gray necrotic node to highlight all source paths pointing to that error page |
| **Diagnostic Report Export** | After scanning, export a JSON report containing "necrotic tissue list" and "structural recommendations" |
| **Dark/Light Theme** | Supports dual theme switching with real-time 3D graph color updates |

---

## Security

This tool includes multi-layer security protection for responsible website scanning:

| Mechanism | Description |
|-----------|-------------|
| **SSRF Protection** | Blocks private IPs, localhost, cloud metadata endpoints, and other dangerous targets |
| **Rate Limiting** | Max 5 requests per IP per minute, max 10 concurrent scans globally |
| **robots.txt Compliance** | Automatically reads and respects target website's robots.txt rules |
| **Exponential Backoff Retry** | Auto-retries on 5xx errors to avoid misjudging temporary failures |
| **Security Headers** | Complete CSP, X-Frame-Options, X-Content-Type-Options, etc. |
| **Input Validation** | Pydantic model validation + frontend double-check |
| **Error Masking** | Error messages automatically strip internal paths, IPs, and sensitive info |

---

## Visual Design

### Color Palette

Strictly controlled to low-saturation calm tones, with a pure deep-sea black background featuring extremely subtle dynamic noise:

| State | Color | Description |
|-------|-------|-------------|
| **Healthy** | Phosphor Green `#22c55e` | Normally functioning pages |
| **Blocked** | Industrial Amber `#d97706` | Response time > 2 seconds |
| **Necrotic** | Dead Gray `#6b7280` | HTTP 4xx/5xx errors |

### Decay Mechanisms

The system triggers gentle but definite physical changes based on crawler results:

| Diagnosis | Threshold | Visual Expression |
|-----------|-----------|-------------------|
| **Digital Gangrene** | HTTP 4xx/5xx | Node turns dead gray, flickers weakly like a broken light bulb, and slowly sinks |
| **Viscous Blockage** | Latency > 2000ms | Semi-transparent amber halo around node, movement trails with heavy drag |
| **Fiber Optic Pulse** | Normal | Line opacity fluctuates, simulating quiet signal conduction in nerve fibers |
| **Orphan Float** | In-degree = 0 | Node opacity decreases, floats at edges, no incoming connections |

### Boot Aesthetics

- **Gradual Emergence**: Nodes and connections gradually emerge, no harsh flashing, protecting visual comfort for long observation sessions

---

## Technical Architecture

### Tech Stack

| Technology | Purpose | Notes |
|------------|---------|-------|
| [FastAPI](https://fastapi.tiangolo.com/) | Backend API + WebSocket | Native WebSocket support |
| [aiohttp](https://docs.aiohttp.org/) | Async crawler | High-performance concurrent requests |
| [BeautifulSoup4](https://www.crummy.com/software/BeautifulSoup/) | HTML parsing | Link extraction |
| [3d-force-graph](https://github.com/vasturiano/3d-force-graph) | 3D force-directed graph | Based on Three.js |
| Vanilla JS | Frameworkless frontend | Modular design |

### Crawling Logic

```
┌─────────────────────────────────────────────────────────┐
│                    Crawling Engine                       │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────┐    ┌──────────────┐    ┌──────────────┐   │
│  │ Start URL│ →  │ DFS Depth    │ →  │ WebSocket    │   │
│  │          │    │ Max 3 levels │    │ Real-time    │   │
│  └──────────┘    └──────────────┘    └──────────────┘   │
│                                                          │
│  Constraints: Same domain, concurrency control, latency  │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### WebSocket Events

| Event | Description |
|-------|-------------|
| `node_discovered` | New page found, frontend immediately creates node |
| `link_discovered` | Link between pages found, frontend creates connection |
| `diagnosis_update` | Returns detailed diagnostic data for that page (status code, response time) |
| `scan_complete` | Scan complete, returns full report |

### Module Structure

| Module | Responsibility |
|--------|----------------|
| `main.py` | FastAPI entry, WebSocket endpoint, logging |
| `crawler.py` | Async crawler engine, robots.txt, retry mechanism |
| `security.py` | SSRF protection, rate limiting, validation, security headers |
| `static/js/graph.js` | 3D force-directed graph rendering, WebGL resource management |
| `static/js/app.js` | Main entry, state management, frontend validation |
| `static/js/theme.js` | Dark/light theme switching |
| `tests/` | 48 unit tests (security module + crawler core logic) |

---

## Diagnostic Logic

| Technical Metric | Threshold | System Trigger |
|------------------|-----------|----------------|
| **HTTP 4xx/5xx** | Necrosis | Node turns gray, stops pulsing, produces sinking gravity |
| **Latency > 2000ms** | Blockage | Node turns amber, connection particle flow slows, produces viscous feel |
| **In-degree = 0** | Orphan | Node opacity decreases, floats at edges, no incoming connections |
| **Out-degree > 50** | Overload | Node produces high-frequency vibration, sprays tiny decorative particles |

---

## Project Structure

```
day-28-site-tomograph/
├── main.py                    # FastAPI entry, WebSocket, logging
├── crawler.py                 # Async crawler engine
├── security.py                # Security module (SSRF, rate limit, validation)
├── templates/
│   └── index.html             # Main page
├── static/
│   ├── css/
│   │   └── style.css          # Dark/light theme styles
│   └── js/
│       ├── graph.js           # 3D force-directed graph rendering
│       ├── theme.js           # Theme switching
│       └── app.js             # Main entry, state management
├── tests/                     # Unit tests
│   ├── test_security.py       # Security module tests
│   └── test_crawler.py        # Crawler logic tests
├── assets/
│   └── preview.webp           # Preview image
├── pyproject.toml             # uv project config
├── uv.lock                    # Dependency lock
├── LICENSE
├── README.md
└── README_EN.md
```

---

## Local Development

```bash
# Clone the repo
git clone https://github.com/tznthou/day-28-site-tomograph.git
cd day-28-site-tomograph

# Install dependencies (using uv)
uv sync

# Start dev server
uv run uvicorn main:app --reload

# Open browser
open http://localhost:8000
```

### Running Tests

```bash
# Install dev dependencies
uv sync --extra dev

# Run all tests
uv run pytest tests/ -v

# Run single test file
uv run pytest tests/test_security.py -v
```

---

## Deployment

This project is deployed on [Zeabur](https://zeabur.com/).

---

## Future Plans

### Completed ✓
- [x] Dark/light theme switching
- [x] Complete security mechanisms (SSRF, rate limiting, input validation)
- [x] Unit test coverage (48 tests)
- [x] Structured logging
- [x] robots.txt compliance
- [x] Error retry mechanism (exponential backoff)

### Visual Enhancements
- [ ] Custom Three.js Shader for "refraction scan plane" effect
- [ ] Particle system optimization, using very low opacity stacking to produce soft glow
- [ ] Sound design: Low-frequency ambient drone + low-pass filter processing

### Feature Expansion
- [ ] Configurable Latency threshold (UI adjustment)
- [ ] Adjustable crawl depth (1-5 levels)
- [ ] Authenticated scanning support (with Cookie/Token)
- [ ] SEO metrics integration (title, description, structured data)

---

## Reflections

### A Simple Need

The core function of this project is actually quite simple: check if a website's links are still alive, and find any broken ones that need fixing.

But I thought, if I'm going to build it anyway, why not present it in an interesting way? Instead of giving a cold list, let people "see" how the website structure grows and where it starts to decay.

### Unexpectedly Fun

The result turned out more interesting than expected. Watching nodes pop up one by one, connections gradually forming, broken spots turning gray and sinking—there's a strangely therapeutic quality to this "observation" process.

Maybe it's because we usually only see results, rarely getting to witness the "process."

### Future Possibilities

The current version is just a starting point. A few directions I'd like to explore:

- Add sound effects, subtle audio when nodes emerge
- More refined visual effects, like vacuum tubes slowly warming up
- Support more diagnostic metrics, beyond just link health

I'll work on these when I have time. I think it could be quite an interesting experience.

---

## License

This work is licensed under [AGPL-3.0](https://www.gnu.org/licenses/agpl-3.0).

This means:
- ✅ Free to use, modify, and distribute
- ✅ Commercial use allowed
- ⚠️ Modified versions must be open source
- ⚠️ Network services must also provide source code

---

## Related Projects

- [Day-20 SEO Roaster](https://github.com/tznthou/day-20-seo-roaster) - SEO critique tool
- [Day-22 Site Portrait](https://github.com/tznthou/day-22-site-portrait) - Website portrait poster
- [Day-23 City Breath](https://github.com/tznthou/day-23-city-breath) - Air quality visualization

---

> **"See the structure to understand the defects; understand the defects to begin the repair."**
