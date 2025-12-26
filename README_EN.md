# Site Tomograph 網站斷層掃描

[![License: AGPL-3.0](https://img.shields.io/badge/License-AGPL--3.0-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104-009688.svg)](https://fastapi.tiangolo.com/)
[![Three.js](https://img.shields.io/badge/Three.js-r158-000000.svg)](https://threejs.org/)
[![3d-force-graph](https://img.shields.io/badge/3d--force--graph-1.73-FF6B6B.svg)](https://github.com/vasturiano/3d-force-graph)

[← Back to Muripo HQ](https://tznthou.github.io/muripo-hq/) | [中文](README.md)

A low-light, high-immersion 3D website structure diagnostic tool. Enter a URL and watch the site topology grow in real-time from the center, intuitively discovering dead links, slow pages, and orphan nodes through visualized "decay mechanisms."

![Site Tomograph](assets/preview.webp)

> **"This isn't just a visual piece—it's a professional diagnostic instrument that lets developers 'see' structural defects in code."**

---

## Core Concept

Traditional website health check tools give you a cold report. This tool lets you **witness** how a website's neural network grows and where it starts to decay.

Using the gradual aesthetics of "vacuum tube warm-up" and the scanning effects of "optical refraction," we've created a space where developers can quietly and comfortably observe the growth and decay of digital organisms.

---

## Features

| Feature | Description |
|---------|-------------|
| **Real-time Topology Growth** | After entering a URL, watch the site structure asynchronously expand outward from the center |
| **Latency Heat Mapping** | Intuitively display page response delays through particle flow speed on connections |
| **Dead Link Tracking** | Click any gray necrotic node to highlight all source paths pointing to that error page |
| **Diagnostic Report Export** | After scanning, export a JSON report containing "necrotic tissue list" and "structural recommendations" |

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

- **Vacuum Tube Warm-up**: Simulates vacuum tube warm-up, light points gradually emerge, no harsh flashing
- **Refraction Scan**: Uses "refraction plane" instead of "laser plane", nodes produce subtle dispersion and displacement as the scan surface passes

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
| `main.py` | FastAPI entry, WebSocket endpoint |
| `crawler.py` | Async crawler engine |
| `static/js/graph.js` | 3D force-directed graph rendering |
| `static/js/effects.js` | Visual effects (decay, pulse) |
| `static/js/app.js` | Main entry, state management |

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
├── main.py                    # FastAPI entry
├── crawler.py                 # Crawler engine
├── templates/
│   └── index.html             # Main page
├── static/
│   ├── css/
│   │   └── style.css          # Dark theme styles
│   └── js/
│       ├── graph.js           # 3D graph rendering
│       ├── effects.js         # Visual effects
│       └── app.js             # Main entry
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

---

## Deployment

This project is deployed on [Zeabur](https://zeabur.com/).

---

## Future Plans

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

### Why "Tomograph"?

Medical CT scans let doctors see the internal structure of the body and find lesions.

Websites also have their "body"—pages are organs, links are blood vessels, response time is blood pressure. When you enter a URL, this tool is like putting the website into a CT scanner, unfolding its internal structure layer by layer.

### The Meaning of Low Light

Harsh light and flashing cause fatigue. Developers often need to stare at screens for long periods while debugging, so this tool deliberately chose a "low-light precision" visual style.

No neon flashing, no explosion effects. Just light points gradually glowing like vacuum tube warm-up, just signals quietly conducting through optical fibers. This is a space where people can focus and think.

### The Aesthetics of Decay

Broken things also have their beauty.

When a node turns gray and starts sinking, you're not just seeing a "404 error"—you're seeing the local necrosis of a digital organism. When a connection becomes viscous and drags a long tail, you feel the signal's difficult journey through that path.

This isn't fear—this is understanding. Only after understanding can we begin to repair.

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
