"""
GIS Infrastructure Exposure & Spatial Overlap Analysis Module.
Overlays pre-event OpenStreetMap infrastructure (roads, bridges, buildings)
with detected flood and debris polygons.
"""
from typing import Dict, Any, List, Tuple
from shapely.geometry import shape, Polygon, LineString, MultiPolygon
from shapely.ops import unary_union
import logging

logger = logging.getLogger(__name__)


class InfrastructureAnalyzer:
    """
    Computes spatial intersections between validated flood/debris polygons
    and pre-event OpenStreetMap infrastructure.
    """

    def analyze_exposure(
        self,
        flood_geojson: Dict[str, Any],
        osm_infrastructure: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Calculates exposure statistics for roads, bridges, and buildings.
        Distinguishes 'potentially affected' spatial overlap from confirmed destruction.
        """
        # Union all flood polygons into a single unified geometry for fast spatial indexing
        flood_polygons = []
        for feat in flood_geojson.get("features", []):
            try:
                geom = shape(feat["geometry"])
                if geom.is_valid:
                    flood_polygons.append(geom)
            except Exception as e:
                logger.debug(f"Invalid flood geometry skipped: {e}")

        if flood_polygons:
            unified_flood_geom = unary_union(flood_polygons)
        else:
            unified_flood_geom = Polygon()

        # 1. Analyze Road Segments & Bridges
        roads_fc = osm_infrastructure.get("roads", {"features": []})
        total_roads_km = 0.0
        affected_roads_km = 0.0
        total_bridges = 0
        affected_bridges = 0
        
        annotated_roads = []
        severed_road_ids = []

        for feat in roads_fc.get("features", []):
            geom = shape(feat["geometry"])
            length_deg = geom.length
            # Approximate km conversion for latitude ~28 deg
            length_km = length_deg * 105.0
            total_roads_km += length_km

            is_bridge = feat["properties"].get("bridge") == "yes"
            if is_bridge:
                total_bridges += 1

            intersects = False
            overlap_length_km = 0.0
            if not unified_flood_geom.is_empty and geom.intersects(unified_flood_geom):
                intersects = True
                intersection_geom = geom.intersection(unified_flood_geom)
                overlap_length_km = intersection_geom.length * 105.0
                affected_roads_km += overlap_length_km
                severed_road_ids.append(feat["id"])
                if is_bridge:
                    affected_bridges += 1

            props = dict(feat["properties"])
            props.update({
                "is_potentially_affected": intersects,
                "overlap_length_km": round(overlap_length_km, 3),
                "total_length_km": round(length_km, 3),
                "damage_classification": "potentially_disrupted" if intersects else "intact",
            })

            annotated_roads.append({
                "type": "Feature",
                "id": feat["id"],
                "properties": props,
                "geometry": feat["geometry"],
            })

        # 2. Analyze Buildings
        buildings_fc = osm_infrastructure.get("buildings", {"features": []})
        total_buildings = 0
        affected_buildings = 0
        annotated_buildings = []

        for feat in buildings_fc.get("features", []):
            geom = shape(feat["geometry"])
            total_buildings += 1
            intersects = False

            if not unified_flood_geom.is_empty and geom.intersects(unified_flood_geom):
                intersects = True
                affected_buildings += 1

            props = dict(feat["properties"])
            props.update({
                "is_potentially_affected": intersects,
                "exposure_status": "in_flood_debris_zone" if intersects else "safe",
            })

            annotated_buildings.append({
                "type": "Feature",
                "id": feat["id"],
                "properties": props,
                "geometry": feat["geometry"],
            })

        return {
            "summary": {
                "total_roads_km": round(total_roads_km, 2),
                "affected_roads_km": round(affected_roads_km, 2),
                "percent_roads_affected": round((affected_roads_km / total_roads_km * 100) if total_roads_km > 0 else 0, 1),
                "total_bridges": total_bridges,
                "affected_bridges": affected_bridges,
                "total_buildings": total_buildings,
                "affected_buildings": affected_buildings,
                "methodology": "Spatial intersection with SAR+Optical validated flood/debris extent",
                "disclaimer": "Metrics represent potential physical exposure and disruption, not verified complete structural demolition.",
            },
            "severed_road_ids": severed_road_ids,
            "annotated_roads": {"type": "FeatureCollection", "features": annotated_roads},
            "annotated_buildings": {"type": "FeatureCollection", "features": annotated_buildings},
        }

