# 3-Minute Demo Presentation Script

**System Name:** AEROSIS — Multimodal Satellite Disaster Intelligence System  
**Presentation Time:** 3 Minutes  
**Audience:** Hackathon Judges, Technical Evaluators, Disaster Responders

---

## [0:00 - 0:20] The Problem & The Remote Sensing Imperative
- *"Distinguished judges, when extreme mountain disasters strike — such as the 26 August 2026 glacial avalanche and debris flood along Nepal's Bhote Koshi–Trishuli corridor — ground sensors are wiped out, telecommunications collapse, and mountain roads are severed.*
- *Responders cannot answer the three most urgent questions: Where did the flood hit? What was damaged? And which villages are cut off?*
- *Our system, AEROSIS, turns raw, free satellite imagery and topological network analysis into actionable disaster intelligence within minutes."*

---

## [0:20 - 0:50] Autonomous Discovery & Multimodal Ingestion (Judge Mode)
- *(Action: Enter AOI bounding box and disaster date 2026-08-26 into the UI)*
- *"AEROSIS is fully generalizable — it is not hardcoded for Trishuli. For any AOI and flood date, our system autonomously queries the Copernicus Data Space Ecosystem.*
- *Crucially, it enforces strict physical SAR geometry: it matches Sentinel-1 radar scenes from the exact same orbital track to prevent mountain terrain distortions.*
- *It pulls Sentinel-2 optical imagery when cloud cover allows, Copernicus WorldDEM-30 for terrain elevation, and extracts a strictly pre-event OpenStreetMap baseline via ohsome."*

---

## [0:50 - 1:20] Multimodal AI Flood & Debris Segmentation
- *(Action: Toggle Sentinel-1 pre/post slider and overlay AI flood segmentation mask)*
- *"Our segmentation pipeline fuses radar backscatter change with multispectral water indices (MNDWI) and DEM slope constraints.*
- *Trained on Kuro Siwo multi-sensor flood benchmarks, the model extracts both standing water and rough debris flows that blanketed the riverbed, avoiding false positives on mountain slopes."*

---

## [1:20 - 1:50] Infrastructure Overlay & Topological Cut-Off Analysis
- *(Action: Zoom in on severed highway bridges and isolated mountain settlements)*
- *"Spatial overlap is not damage. AEROSIS separates potential exposure from true operational isolation.*
- *We construct a topological road network graph from pre-event OSM. When detected flood zones sever critical road segments, our routing engine recalculates reachability to the nearest district hospital.*
- *As you see on screen, Village B and Village C are highlighted in red as CUT OFF — not just because the flood touched them, but because their sole road access to the hospital has been completely severed."*

---

## [1:50 - 2:20] Situation Report & Bilingual AI Copilot
- *(Action: Display generated 1-page SitRep and ask the Copilot in English and Nepali)*
- *"Responders receive a generated one-page Situation Report with verifiable numbers directly derived from our computational pipeline.*
- *Our bilingual AI Copilot allows field personnel to query in English and Nepali: 'कुन कुन गाउँहरू सम्पर्कविहीन भएका छन्?' (Which villages are cut off?).*
- *Every response is strictly grounded in `analysis_result.json` — hallucination of victim counts or damaged numbers is mathematically impossible."*

---

## [2:20 - 2:40] Bonus Flow-Path Tracing & EMSR927 Validation
- *(Action: Click upstream trigger point to trace downstream path, then show validation tab)*
- *"Using our DEM flow-path tracer, responders can click any upstream glacial source to model downstream valley exposure.*
- *For scientific rigor, we validated our Trishuli detection post-hoc against Copernicus EMS EMSR927, achieving high spatial alignment without ever using reference maps during inference."*

---

## [2:40 - 3:00] Limitations & Responsible AI Conclusion
- *"AEROSIS is an educational prototype. We explicitly document our limitations: satellite revisit latency means we are a rapid post-event mapping system, not a real-time warning sensor.*
- *With zero proprietary barriers and 100% open data compliance, AEROSIS provides rapid, reproducible, life-saving intelligence when it matters most. Thank you."*

