"""
Cut-Off Settlement Connectivity & Routing Engine.
Determines which settlements have lost road access to designated district hospitals or towns.
Generates before-vs-after routing analysis.
"""
from typing import Dict, Any, List, Optional, Tuple
import networkx as nx
from src.network.road_graph import RoadGraphBuilder
from src.utils.geo_utils import haversine_distance


class CutOffAnalyzer:
    """
    Analyzes pre-event vs post-event topological shortest path reachability
    between settlements and critical facilities (hospitals / district centers).
    """

    def __init__(self, graph_builder: Optional[RoadGraphBuilder] = None):
        self.builder = graph_builder or RoadGraphBuilder()

    def analyze_connectivity(
        self,
        annotated_roads_fc: Dict[str, Any],
        settlements_fc: Dict[str, Any],
        destination_hospital_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Builds pre-event baseline graph and post-event damaged graph (with severed edges removed).
        Calculates shortest path reachability from each village to the destination hospital.
        """
        pre_graph, node_coords = self.builder.build_graph(annotated_roads_fc)
        
        # Build post-event graph by removing severed edges
        post_graph = pre_graph.copy()
        severed_edges = []
        for u, v, data in list(post_graph.edges(data=True)):
            if data.get("is_severed", False):
                severed_edges.append((u, v, data.get("name", "Unnamed Road")))
                post_graph.remove_edge(u, v)

        # Identify hospital / target hub node
        hospital_feature = None
        for feat in settlements_fc.get("features", []):
            props = feat.get("properties", {})
            if props.get("amenity") == "hospital" or "hospital" in props.get("name", "").lower():
                hospital_feature = feat
                break
        
        if not hospital_feature and settlements_fc.get("features"):
            # Default to first feature as destination hub
            hospital_feature = settlements_fc["features"][0]

        hosp_coords = hospital_feature["geometry"]["coordinates"]
        hosp_lat, hosp_lon = hosp_coords[1], hosp_coords[0]
        hosp_node = self.builder.find_nearest_node((hosp_lat, hosp_lon), node_coords)
        hospital_name = hospital_feature["properties"].get("name", "District Hospital")

        settlement_results = []
        isolated_count = 0
        connected_count = 0

        for feat in settlements_fc.get("features", []):
            props = feat.get("properties", {})
            # Skip the hospital itself from settlement list
            if feat["id"] == hospital_feature["id"]:
                continue

            coords = feat["geometry"]["coordinates"]
            v_lat, v_lon = coords[1], coords[0]
            v_node = self.builder.find_nearest_node((v_lat, v_lon), node_coords)
            v_name = props.get("name", "Unknown Village")
            population = props.get("population", 500)

            # Pre-event shortest path
            pre_route_km = None
            pre_path_nodes = []
            if nx.has_path(pre_graph, v_node, hosp_node):
                pre_dist_m = nx.shortest_path_length(pre_graph, v_node, hosp_node, weight="length_meters")
                pre_route_km = round(pre_dist_m / 1000.0, 2)
                pre_path_nodes = nx.shortest_path(pre_graph, v_node, hosp_node, weight="length_meters")

            # Post-event shortest path
            post_route_km = None
            post_path_nodes = []
            is_cut_off = True
            detour_km = 0.0
            disconnection_reason = "No severed roads"

            if nx.has_path(post_graph, v_node, hosp_node):
                post_dist_m = nx.shortest_path_length(post_graph, v_node, hosp_node, weight="length_meters")
                post_route_km = round(post_dist_m / 1000.0, 2)
                post_path_nodes = nx.shortest_path(post_graph, v_node, hosp_node, weight="length_meters")
                is_cut_off = False
                connected_count += 1
                if pre_route_km:
                    detour_km = round(max(0.0, post_route_km - pre_route_km), 2)
                status_text = "CONNECTED"
            else:
                is_cut_off = True
                isolated_count += 1
                status_text = "CUT_OFF"
                disconnection_reason = f"Primary road link severed by flood/debris across downstream river corridor."

            # Construct coordinate path geometry for GeoJSON
            pre_route_coords = [[node_coords[n][1], node_coords[n][0]] for n in pre_path_nodes if n in node_coords]
            post_route_coords = [[node_coords[n][1], node_coords[n][0]] for n in post_path_nodes if n in node_coords]

            settlement_results.append({
                "id": feat["id"],
                "name": v_name,
                "population": population,
                "status": status_text,
                "is_cut_off": is_cut_off,
                "nearest_hospital": hospital_name,
                "pre_event_distance_km": pre_route_km,
                "post_event_distance_km": post_route_km,
                "detour_increase_km": detour_km,
                "disconnection_reason": disconnection_reason,
                "coordinates": [v_lon, v_lat],
                "pre_route_geojson": {
                    "type": "LineString",
                    "coordinates": pre_route_coords
                } if pre_route_coords else None,
                "post_route_geojson": {
                    "type": "LineString",
                    "coordinates": post_route_coords
                } if post_route_coords else None,
            })

        # GeoJSON output for dashboard visualization
        settlement_markers = []
        for s in settlement_results:
            settlement_markers.append({
                "type": "Feature",
                "id": s["id"],
                "properties": {
                    "name": s["name"],
                    "status": s["status"],
                    "population": s["population"],
                    "is_cut_off": s["is_cut_off"],
                    "destination": s["nearest_hospital"],
                    "pre_dist_km": s["pre_event_distance_km"],
                    "post_dist_km": s["post_event_distance_km"],
                    "detour_km": s["detour_increase_km"],
                    "reason": s["disconnection_reason"],
                },
                "geometry": {
                    "type": "Point",
                    "coordinates": s["coordinates"],
                }
            })

        return {
            "summary": {
                "total_settlements": len(settlement_results),
                "cut_off_settlements_count": isolated_count,
                "connected_settlements_count": connected_count,
                "destination_hospital": hospital_name,
                "isolated_population": sum(s["population"] for s in settlement_results if s["is_cut_off"]),
            },
            "settlements": settlement_results,
            "settlements_geojson": {
                "type": "FeatureCollection",
                "features": settlement_markers,
            },
            "severed_edge_count": len(severed_edges),
            "provenance": "NetworkX Topological Road Network Shortest Path Analysis",
        }

