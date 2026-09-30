"""
Sentinel-1 SAR Preprocessing and Radiometric Calibration Module.
Handles dual-polarization calibration (VV, VH), speckle filtering, and topographic slope masking.
"""
from typing import Dict, Any, Tuple, Optional
import numpy as np
from scipy.ndimage import uniform_filter


class SARPreprocessor:
    """
    Preprocesses Sentinel-1 SAR GRD imagery with radiometric calibration,
    speckle noise suppression, and terrain slope masking.
    """

    def __init__(self, filter_window_size: int = 5):
        self.window_size = filter_window_size

    def calibrate_and_filter(
        self,
        raw_intensity: np.ndarray,
        apply_speckle_filter: bool = True,
        eps: float = 1e-7,
    ) -> np.ndarray:
        """
        Converts linear intensity to backscatter coefficient sigma0 (dB)
        and applies an enhanced Lee-style speckle filter.
        """
        # Ensure positive values
        safe_intensity = np.maximum(raw_intensity, eps)
        
        if apply_speckle_filter:
            # Lee-like spatial filter using local mean and variance
            mean = uniform_filter(safe_intensity, size=self.window_size)
            mean_sq = uniform_filter(safe_intensity**2, size=self.window_size)
            variance = np.maximum(mean_sq - mean**2, 0)
            
            # Weight calculation
            overall_variance = np.var(safe_intensity) + eps
            weight = variance / (variance + overall_variance)
            filtered = mean + weight * (safe_intensity - mean)
            safe_intensity = np.maximum(filtered, eps)

        # Convert to decibels (dB)
        sigma0_db = 10.0 * np.log10(safe_intensity)
        return sigma0_db

    def process_dual_pol_scene(
        self,
        vv_intensity: np.ndarray,
        vh_intensity: np.ndarray,
        slope_degrees: Optional[np.ndarray] = None,
        max_slope_thresh: float = 35.0,
    ) -> Dict[str, np.ndarray]:
        """
        Processes both VV and VH channels and applies mountain slope masking.
        """
        vv_db = self.calibrate_and_filter(vv_intensity)
        vh_db = self.calibrate_and_filter(vh_intensity)
        
        # Cross-ratio: VH - VV in dB represents volumetric / roughness change
        cross_ratio_db = vh_db - vv_db

        # Topographic validity mask (slopes <= max_slope_thresh)
        valid_terrain_mask = np.ones_like(vv_db, dtype=bool)
        if slope_degrees is not None:
            valid_terrain_mask = (slope_degrees <= max_slope_thresh)

        return {
            "vv_db": vv_db,
            "vh_db": vh_db,
            "cross_ratio_db": cross_ratio_db,
            "valid_terrain_mask": valid_terrain_mask,
        }
