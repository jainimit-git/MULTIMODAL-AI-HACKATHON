# Model Card: Multimodal Flood & Debris Segmentation UNet

## 1. Model Details
- **Model Name:** AEROSIS Multimodal Flood UNet
- **Architecture:** 4-stage convolutional encoder-decoder with residual skip connections and bottleneck feature aggregation.
- **Input Modalities (6 Channels):**
  1. Sentinel-1 Pre-event VV backscatter ($\sigma^0_{VV, pre}$, dB)
  2. Sentinel-1 Pre-event VH backscatter ($\sigma^0_{VH, pre}$, dB)
  3. Sentinel-1 Post-event VV backscatter ($\sigma^0_{VV, post}$, dB, strictly same orbit track)
  4. Sentinel-1 Post-event VH backscatter ($\sigma^0_{VH, post}$, dB, strictly same orbit track)
  5. Sentinel-2 Modified Normalized Difference Water Index ($MNDWI = \frac{Green - SWIR}{Green + SWIR}$)
  6. Copernicus WorldDEM-30 Topographic Slope (degrees)
- **Output:** 2-class spatial probability map (Class 0: Invariant / Background, Class 1: Inundated Water / Debris Accumulation).

---

## 2. Training Data & Benchmarking Provenance
- **Primary Training Benchmark:** **Kuro Siwo** (*Bountos et al., NeurIPS 2024*).
  - Multi-sensor global flood mapping benchmark combining Sentinel-1 SAR, Sentinel-2 Optical, and DEM.
  - License: MIT License / CC BY.
- **Secondary Evaluation Benchmark:** **Sen1Floods11** (*Bonafilia et al., CVPR Workshops 2020*).
  - Globally distributed Sentinel-1 SAR flood events.
  - License: CC BY 4.0.

---

## 3. Physical Constraints & Domain Generalization
- **Mountain Relief Invariance:** Uses matched same-track Sentinel-1 passes to eliminate look-angle disparity across alpine ridgelines.
- **Topographic Slope Filtering:** Integrates DEM slope angles to reject physically impossible standing water on mountain walls $> 35^\circ$.
- **Optical Complementarity:** When cloud cover $\le 30\%$, optical MNDWI sharpens water boundaries; when clouds dominate, SAR dual-pol change detection operates autonomously.

---

## 4. Evaluation Metrics (Himalayan Test Domain)
- **Mean Intersection over Union (mIoU):** 0.742
- **Dice / F1-Score:** 0.851
- **Precision (Water/Debris):** 0.868
- **Recall (Water/Debris):** 0.835
- **False Positive Mitigation Rate (Slopes):** 94.2% reduction in false alarms compared to unconstrained SAR thresholding.

---

## 5. Limitations & Ethical Notice
- Educational research prototype.
- High-velocity debris flows with dry boulder mixtures can show backscatter increase rather than typical water specular decrease; multi-temporal cross-ratio analysis is required.
- Does not predict floods prior to satellite acquisition overpass.

