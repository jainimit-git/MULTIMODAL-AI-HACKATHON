"""
Geospatial math and transformation utilities.
"""
from typing import List, Tuple, Union, Dict, Any
import math
import numpy as np
from shapely.geometry import shape, mapping, Polygon, MultiPolygon


def validate_bbox(bbox: Union[List[float], Tuple[float, float, float, float]]) -> bool:
    """
    Validates that a bounding box is formatted as [min_lon, min_lat, max_lon, max_lat]
    and contains valid geographic coordinates.
    """
    if len(bbox) != 4:
        raise ValueError(f"Bounding box must have 4 elements, got {len(bbox)}")
    min_lon, min_lat, max_lon, max_lat = bbox

    if not (-180.0 <= min_lon <= 180.0 and -180.0 <= max_lon <= 180.0):
        raise ValueError(f"Longitudes must be between -180 and 180, got ({min_lon}, {max_lon})")
    if not (-90.0 <= min_lat <= 90.0 and -90.0 <= max_lat <= 90.0):
        raise ValueError(f"Latitudes must be between -90 and 90, got ({min_lat}, {max_lat})")
    if min_lon >= max_lon:
        raise ValueError(f"min_lon ({min_lon}) must be strictly less than max_lon ({max_lon})")
    if min_lat >= max_lat:
        raise ValueError(f"min_lat ({min_lat}) must be strictly less than max_lat ({max_lat})")

    return True


def bbox_to_polygon(bbox: Union[List[float], Tuple[float, float, float, float]]) -> Polygon:
    """
    Converts a [min_lon, min_lat, max_lon, max_lat] bounding box to a Shapely Polygon.
    """
    validate_bbox(bbox)
    min_lon, min_lat, max_lon, max_lat = bbox
    return Polygon([
        (min_lon, min_lat),
        (max_lon, min_lat),
        (max_lon, max_lat),
        (min_lon, max_lat),
        (min_lon, min_lat)
    ])


def haversine_distance(coord1: Tuple[float, float], coord2: Tuple[float, float]) -> float:
    """
    Calculates the great-circle distance between two points on the Earth surface in meters.
    coord1: (lat1, lon1)
    coord2: (lat2, lon2)
    """
    lat1, lon1 = coord1
    lat2, lon2 = coord2

    R = 6371000.0  # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (math.sin(delta_phi / 2.0) ** 2 +
         math.cos(phi1) * math.cos(phi2) * (math.sin(delta_lambda / 2.0) ** 2))
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))

    return R * c


def calculate_iou(mask_pred: np.ndarray, mask_true: np.ndarray) -> float:
    """
    Computes Intersection over Union (Jaccard Index) for binary segmentation masks.
    """
    if mask_pred.shape != mask_true.shape:
        raise ValueError(f"Shape mismatch: {mask_pred.shape} vs {mask_true.shape}")

    pred_bool = mask_pred.astype(bool)
    true_bool = mask_true.astype(bool)

    intersection = np.logical_and(pred_bool, true_bool).sum()
    union = np.logical_or(pred_bool, true_bool).sum()

    if union == 0:
        return 1.0 if intersection == 0 else 0.0

    return float(intersection / union)


def calculate_dice_f1(mask_pred: np.ndarray, mask_true: np.ndarray) -> float:
    """
    Computes Dice coefficient / F1-score for binary segmentation masks.
    """
    if mask_pred.shape != mask_true.shape:
        raise ValueError(f"Shape mismatch: {mask_pred.shape} vs {mask_true.shape}")

    pred_bool = mask_pred.astype(bool)
    true_bool = mask_true.astype(bool)

    intersection = np.logical_and(pred_bool, true_bool).sum()
    total_positives = pred_bool.sum() + true_bool.sum()

    if total_positives == 0:
        return 1.0

    return float(2.0 * intersection / total_positives)


def reproject_geojson_wgs84_to_utm(geojson_geom: Dict[str, Any], utm_epsg: int = 32645) -> Dict[str, Any]:
    """
    Reprojects GeoJSON geometry dictionary from EPSG:4326 to UTM.
    """
    from pyproj import Transformer
    transformer = Transformer.from_crs("EPSG:4326", f"EPSG:{utm_epsg}", always_xy=True)
    
    geom = shape(geojson_geom)
    
    def transform_coords(x, y, z=None):
        return transformer.transform(x, y)

    from shapely.ops import transform
    projected = transform(transform_coords, geom)
    return mapping(projected)
