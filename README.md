# WIIINGS

WIIINGS is a high-performance, real-time tactical flight tracking dashboard designed to intercept, process, and map spatial telemetry frames. 

## 🛰️ Architecture Overview

The application is architected around a decoupling pattern balancing speed, historical integrity, and real-time frontend streaming synchronization:

1. **Ingestion Deck (`producer.py`)**: Continuously monitors international airspace, fetching high-fidelity aircraft state vectors.
2. **Stream Transport (Apache Kafka)**: Acts as the decoupled, fault-tolerant message broker handling telemetry streams at scale.
3. **Storage & Spatial Compute (PostgreSQL + PostGIS)**: Captures incoming coordinates into structural geographic instances (`GEOMETRY(Point, 4326)`), instantly extracting dynamic metrics.
4. **Knowledge Layer (Neo4j)**: Correlates aircraft vectors, corporate entities, and geographic sectors into a complex operational knowledge graph.
5. **Operational Console (`app.py`)**: A lightweight Flask orchestration server serving an absolute-positioned Single Page Application (SPA) driven by Leaflet.js with long-polling telemetry sockets.

---

## 🛠️ Tech Stack Matrix

| Component | Technology | Role |
| :--- | :--- | :--- |
| **Backend Engine** | Python 3.x / Flask | REST API & Web Orchestration |
| **Spatial Database** | PostgreSQL / PostGIS | Persistent Telemetry & Geometric Queries |
| **Graph Database** | Neo4j | Asset Inter-connectivity & Intelligence Graph |
| **Message Broker** | Apache Kafka | Real-time Data Streaming Pipeline |
| **Frontend Mapping**| Leaflet.js | Canvas-based Tactical Geospatial Rendering |
| **UI Styling** | Vanilla CSS3 / HTML5 | Glassmorphism Responsive HUD Panel |

---

## ⚡ UI Features

* **Single-Page Application Portal**: Seamless initialization deck featuring a high-impact terminal launch control (`Let's Fly`).
* **Tactical Amber Interface**: Immersive neon command center theme optimized for high-contrast tracking environments.
* **Animated Telemetry Card**: Dynamic absolute-positioned intelligence card with smooth entry and exit sliding frames.
* **Responsive Layout Grid**: Adapts seamlessly from ultra-wide terminal monitors to mobile viewports via fluid CSS breakpoints.
* **Custom Flight Favicon**: Integrated vector inline data URI mapping aircraft telemetry indicators directly to the browser tab.

---

## 🚀 Local Installation & Deployment

### 1. Clone the Tracking Core
```bash
git clone [https://github.com/suyashaditya919/WIIINGS.git](https://github.com/suyashaditya919/WIIINGS.git)
cd wiiings
