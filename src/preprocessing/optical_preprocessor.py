"""
Sentinel-2 Optical Preprocessor & Spectral Index Calculator.
Calculates Modified Normalized Difference Water Index (MNDWI), NDWI, and NDVI.
"""
from typing import Dict, Any, Optional
import numpy as np


class OpticalPreprocessor:
    """
    Computes standard remote sensing indices for water, moisture, and vegetation.
    """

    def compute_indices(
        self,
        green: np.ndarray,
        red: np.ndarray,
        nir: np.ndarray,
        swir: np.ndarray,
        eps: float = 1e-7,
    ) -> Dict[str, np.ndarray]:
        """
        Computes MNDWI, NDWI, and NDVI spectral indices.
        - MNDWI = (Green - SWIR) / (Green + SWIR + eps)
        - NDWI  = (Green - NIR)  / (Green + NIR + eps)
        - NDVI  = (NIR - Red)    / (NIR + Red + eps)
        """
        # Modified Normalized Difference Water Index (Xu, 2006)
        mndwi = (green - swir) / (green + swir + eps)
        mndwi = np.clip(mndwi, -1.0, 1.0)

        # Standard NDWI (McFeeters, 1996)
        ndwi = (green - nir) / (green + nir + eps)
        ndwi = np.clip(ndwi, -1.0, 1.0)

        # Normalized Difference Vegetation Index
        ndvi = (nir - red) / (nir + red + eps)
        ndvi = np.clip(ndvi, -1.0, 1.0)

        # Binary water indicator from MNDWI
        water_mask = (mndwi > 0.15).astype(np.uint8)

        return {
            "mndwi": mndwi,
            "ndwi": ndwi,
            "ndvi": ndvi,
            "water_mask": water_mask,
        }

