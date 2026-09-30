"""
Sentinel-1 SAR Same-Orbit Change Detection Engine.
Enforces physical radiometric difference on matched viewing geometries.
"""
from typing import Dict, Any, Optional
import numpy as np


class SARChangeDetector:
    """
    Computes calibrated backscatter change between same-orbit Sentinel-1 acquisitions.
    Detects smooth water specular reflection (backscatter drop) and rough debris accumulation (texture change).
    """

    def __init__(self, water_drop_threshold_db: float = -2.5, debris_increase_threshold_db: float = 3.0):
        self.water_threshold_db = water_drop_threshold_db
        self.debris_threshold_db = debris_increase_threshold_db

    def detect_change(
        self,
        pre_vv_db: np.ndarray,
        pre_vh_db: np.ndarray,
        post_vv_db: np.ndarray,
        post_vh_db: np.ndarray,
        slope_mask: Optional[np.ndarray] = None,
    ) -> Dict[str, np.ndarray]:
        """
        Computes delta backscatter in decibels:
        delta_VV = post_VV - pre_VV
        delta_VH = post_VH - pre_VH
        """
        delta_vv = post_vv_db - pre_vv_db
        delta_vh = post_vh_db - pre_vh_db

        # Inundated / smooth water areas typically exhibit a sharp drop in backscatter
        water_change = (delta_vv < self.water_threshold_db) | (delta_vh < self.water_threshold_db)

        # Rough debris flows / eroded mud deposited over smooth soil or vegetation exhibit backscatter anomalies
        debris_change = (delta_vh > self.debris_threshold_db) & (delta_vv > 1.5)

        # Combined raw change mask
        combined_change = water_change | debris_change

        # Apply terrain slope constraint
        if slope_mask is not None:
            combined_change = combined_change & (~slope_mask.astype(bool))
            water_change = water_change & (~slope_mask.astype(bool))
            debris_change = debris_change & (~slope_mask.astype(bool))

        # Relative change magnitude (normalized confidence score 0.0 - 1.0)
        change_magnitude = np.abs(delta_vv) + np.abs(delta_vh)
        normalized_confidence = np.clip(change_magnitude / 10.0, 0.0, 1.0)

        return {
            "delta_vv_db": delta_vv,
            "delta_vh_db": delta_vh,
            "water_change_mask": water_change.astype(np.uint8),
            "debris_change_mask": debris_change.astype(np.uint8),
            "flood_debris_mask": combined_change.astype(np.uint8),
            "change_confidence": normalized_confidence,
        }
