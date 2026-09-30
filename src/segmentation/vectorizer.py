"""
Morphological Cleaning & Vector Polygonization Module.
Converts binary raster flood masks into clean geospatial polygons.
"""
from typing import Dict, Any, List, Tuple, Optional
import numpy as np
from scipy.ndimage import binary_opening, binary_closing, label
from shapely.geometry import Polygon, MultiPolygon, box
from shapely.ops import unary_union


class MaskVectorizer:
    """
    Cleans noisy raster pixels and converts detected flood/debris masks
    into standardized GeoJSON FeatureCollection polygons.
    """

    def __init__(self, min_pixel_area: int = 6, morph_kernel_size: int = 3):
        self.min_pixel_area = min_pixel_area
        self.kernel = np.ones((morph_kernel_size, morph_kernel_size), dtype=bool)

    def clean_mask(self, raw_binary_mask: np.ndarray) -> np.ndarray:
        """
        Applies morphological opening (removes isolated speckles)
        and closing (closes small interior holes).
        """
        bool_mask = raw_binary_mask.astype(bool)
        opened = binary_opening(bool_mask, structure=self.kernel)
        closed = binary_closing(opened, structure=self.kernel)
        
        # Remove connected components smaller than min_pixel_area
        labeled, num_features = label(closed)
        cleaned = np.zeros_like(closed, dtype=np.uint8)
        
        for i in range(1, num_features + 1):
            component = (labeled == i)
            if component.sum() >= self.min_pixel_area:
                cleaned[component] = 1

        return cleaned

    def vectorize_to_geojson(
        self,
        cleaned_mask: np.ndarray,
        bbox: List[float],
        pixel_confidence: Optional[np.ndarray] = None,
    ) -> Dict[str, Any]:
        """
        Converts the binary grid into georeferenced GeoJSON polygons.
        bbox: [min_lon, min_lat, max_lon, max_lat]
        """
        min_lon, min_lat, max_lon, max_lat = bbox
        ny, nx = cleaned_mask.shape
        dlon = (max_lon - min_lon) / nx
        dlat = (max_lat - min_lat) / ny

        labeled, num_features = label(cleaned_mask)
        features: List[Dict[str, Any]] = []

        for feat_id in range(1, num_features + 1):
            component = (labeled == feat_id)
            pixel_count = int(component.sum())
            if pixel_count < self.min_pixel_area:
                continue

            # Compute bounding box of the component
            y_indices, x_indices = np.where(component)
            min_x, max_x = np.min(x_indices), np.max(x_indices)
            min_y, max_y = np.min(y_indices), np.max(y_indices)

            poly_min_lon = min_lon + min_x * dlon
            poly_max_lon = min_lon + (max_x + 1) * dlon
            poly_max_lat = max_lat - min_y * dlat
            poly_min_lat = max_lat - (max_y + 1) * dlat

            poly_geom = box(poly_min_lon, poly_min_lat, poly_max_lon, poly_max_lat)

            # Calculate confidence
            conf_val = 0.85
            if pixel_confidence is not None:
                conf_val = float(np.mean(pixel_confidence[component]))

            features.append({
                "type": "Feature",
                "id": f"flood_polygon_{feat_id}",
                "properties": {
                    "feature_type": "flood_debris_extent",
                    "pixel_count": pixel_count,
                    "estimated_area_m2": round(pixel_count * (dlon * 111000) * (dlat * 111000), 2),
                    "confidence": round(conf_val, 3),
                    "status": "potentially_affected_zone",
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [list(poly_geom.exterior.coords)],
                },
            })

        return {
            "type": "FeatureCollection",
            "features": features,
            "total_polygons": len(features),
            "provenance": "Multimodal AI Flood Segmentation & Vectorizer",
        }
