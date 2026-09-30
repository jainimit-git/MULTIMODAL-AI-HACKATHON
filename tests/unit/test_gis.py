"""
Unit tests for GIS infrastructure exposure and overlay analysis.
"""
from src.gis.infrastructure_analyzer import InfrastructureAnalyzer
from src.acquisition.osm_client import OSMPreEventClient
from src.segmentation.vectorizer import MaskVectorizer
import numpy as np


def test_infrastructure_exposure_analysis():
    analyzer = InfrastructureAnalyzer()
    osm_client = OSMPreEventClient()
    bbox = [85.15, 27.85, 85.45, 28.25]
    infra = osm_client.extract_pre_event_infrastructure(bbox)

    # Create a synthetic flood polygon that covers the main highway bridge (Betrawati)
    mid_lon = 85.30
    min_lat = 27.85
    flood_fc = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [mid_lon - 0.03, min_lat + 0.07],
                        [mid_lon + 0.03, min_lat + 0.07],
                        [mid_lon + 0.03, min_lat + 0.09],
                        [mid_lon - 0.03, min_lat + 0.09],
                        [mid_lon - 0.03, min_lat + 0.07],
                    ]]
                }
            }
        ]
    }

    result = analyzer.analyze_exposure(flood_fc, infra)
    summary = result["summary"]

    assert summary["total_roads_km"] > 0
    assert summary["affected_roads_km"] > 0
    assert summary["total_bridges"] >= 2
    assert summary["affected_bridges"] >= 1
    assert len(result["severed_road_ids"]) >= 1
