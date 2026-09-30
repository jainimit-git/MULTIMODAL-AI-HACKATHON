# AEROSIS — Multimodal Satellite Disaster Intelligence System
### Mapping Flood & Debris Damage From Space

[![CI / Automated Quality Control](https://github.com/jainimit-git/MULTIMODAL-AI-HACKATHON/actions/workflows/tests.yml/badge.svg)](https://github.com/jainimit-git/MULTIMODAL-AI-HACKATHON/actions/workflows/tests.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Open Access Data](https://img.shields.io/badge/Copernicus-Open%20Access-green.svg)](https://dataspace.copernicus.eu/)

> **Educational Prototype Notice:** This system is developed for the *IIT Mandi Multimodal AI Hackathon* as an educational research prototype and is not certified as an operational emergency-response warning platform.

---

## 1. Problem Statement
When high-altitude glacial avalanches, cloudbursts, or dam breaches strike steep mountain valleys (such as the **August 2026 Trishuli Flood, Nepal**), ground telemetry and terrestrial communications are obliterated. Responders urgently need verified answers:
1. **Where did the flood hit?** (Accurate flood and debris spatial delineation despite dense monsoon cloud cover).
2. **What was damaged?** (Spatial exposure assessment of critical infrastructure: buildings, bridges, and highways).
3. **Who is cut off?** (Topological network isolation analysis identifying villages that have lost road connectivity to medical and administrative hubs).

---

## 2. System Architecture & Multimodal Workflow

AEROSIS unifies Synthetic Aperture Radar (SAR), Optical Multispectral Imagery, Digital Elevation Models (DEM), and OpenStreetMap (OSM) topological road graphs into an end-to-end automated intelligence pipeline.

```
USER / JUDGE INPUT: [AOI Bounding Box + Disaster Date]
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│ 1. Autonomous Data Discovery (src/acquisition)               │
│    • Sentinel-1 SAR (Same-Orbit Track Matching)             │
│    • Sentinel-2 MSI (Cloud-Filtered <= 30%)                 │
│    • Copernicus WorldDEM-30 Elevation                       │
│    • Pre-Event OpenStreetMap Snapshot (ohsome v1 adapter)   │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. Multimodal Preprocessing & Radiometric Calibration       │
│    • S1 VV/VH Dual-Pol Calibration & Topographic Masking    │
│    • S2 Spectral Water Indices (MNDWI, NDWI, NDVI)          │
│    • DEM Slope, Aspect, and Terrain Flow Routing            │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. Multimodal AI Flood & Debris Segmentation                │
│    • Dual-Orbit SAR Backscatter Difference / Ratio Engine   │
│    • Multimodal UNet Segmentation (Kuro Siwo Benchmarked)   │
│    • Morphological Vector Cleaning & Polygonization         │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. GIS Infrastructure & Road Network Routing (src/network)  │
│    • Spatial Overlap Analysis (Roads, Bridges, Buildings)   │
│    • Topological Road Graph Construction (NetworkX)         │
│    • Post-Disaster Shortest Path Routing (Dijkstra)         │
│    • Cut-Off Settlement Isolation Identification            │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. Situation Intelligence & Interfaces                      │
│    • Verifiable JSON Metrics (`analysis_result.json`)       │
│    • One-Page Automated Situation Report (Deterministic)    │
│    • Grounded Bilingual Copilot (English & Nepali)          │
│    • Interactive Map Dashboard (MapLibre GL / Leaflet)      │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Strict Data Provenance & Compliance

| Dataset | Role in System | Source / API | License |
| :--- | :--- | :--- | :--- |
| **Sentinel-1 SAR** | **Primary Input** (Cloud-penetrating change detection) | Copernicus Data Space Ecosystem | Copernicus Open Access |
| **Sentinel-2 MSI** | **Complementary Input** (Optical validation & indices) | Copernicus Data Space Ecosystem | Copernicus Open Access |
| **Copernicus WorldDEM-30** | **Input** (Slope constraint & Flow-path bonus) | Copernicus DEM GLO-30 | Copernicus Open Licence |
| **Pre-Event OSM** | **Input** (Baseline infrastructure & Road graph) | ohsome API v1 (Snapshot $\le$ 2026-07-27) | ODbL 1.0 |
| **Kuro Siwo** | **Training / Benchmark** (Flood segmentation model) | Orion AI Lab (NeurIPS 2024) | MIT / CC BY |
| **Copernicus EMS EMSR927**| **Validation ONLY** (Post-hoc benchmark comparison) | Copernicus Emergency Management Service | EMS Open Data |

> **STRICT COMPLIANCE GUARANTEE:**
> - Neither Copernicus EMS (EMSR927) nor UNOSAT damage maps are ever used as inference inputs.
> - Post-event OpenStreetMap edits are strictly filtered out to prevent retrospective bias.
> - Detailed provenance rules are tracked in [`docs/DATA_PROVENANCE.md`](docs/DATA_PROVENANCE.md) and [`docs/COMPLIANCE_CHECKLIST.md`](docs/COMPLIANCE_CHECKLIST.md).

---

## 4. Quick Start & Installation

### Prerequisites
- Python 3.10+ (Tested on Python 3.11 / 3.14)
- Node.js 18+ & npm (for UI dashboard)

### 1. Clone & Set Up Python Environment
```bash
git clone https://github.com/jainimit-git/MULTIMODAL-AI-HACKATHON.git
cd MULTIMODAL-AI-HACKATHON

# Create and activate virtual environment
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment Variables
```bash
cp .env.example .env
# Edit .env with your Copernicus Data Space Ecosystem credentials (optional for offline fixtures)
```

### 3. Run the Automated Test Suite
```bash
pytest tests/ -v
```

### 4. Launch the Backend API & Server
```bash
uvicorn backend.main:app --reload --port 8000
```

---

## 5. Case Study: August 2026 Trishuli Flood, Nepal

To run the Trishuli benchmark pipeline end-to-end:
```bash
python scripts/run_pipeline.py --config config/trishuli.yaml
```

To run in **Judge Live Evaluation Mode** with an arbitrary AOI and date:
```bash
python scripts/run_pipeline.py --aoi 85.15,27.85,85.45,28.25 --date 2026-08-26
```

---

## 6. Required Attributions & Citations

This project adheres strictly to mandatory attribution requirements:

- *"Contains modified Copernicus Sentinel data 2026."*
- *"Produced using Copernicus WorldDEM-30 © DLR e.V. 2010–2014 and © Airbus Defence and Space GmbH 2014–2018 provided under COPERNICUS by the European Union and ESA; all rights reserved."*
- *"© OpenStreetMap contributors."*

### Academic Citations
- **Kuro Siwo:** Bountos, N. I., et al. (2024). *Kuro Siwo: A Global Multi-sensor SAR-Optical-DEM Dataset for Flood Mapping*. Advances in Neural Information Processing Systems (NeurIPS 2024).
- **Sen1Floods11:** Bonafilia, D., et al. (2020). *Sen1Floods11: A Georeferenced Dataset to Train and Test Deep Learning Flood Algorithms for Sentinel-1*. IEEE/CVF CVPR Workshops 2020.
- **Copernicus EMS:** European Union, Copernicus Emergency Management Service data (EMSR927 activation).

---

## 7. Project Memory & Continuity
For continuous agent development and session handoffs, see [`state/PROJECT_STATUS.md`](state/PROJECT_STATUS.md).
