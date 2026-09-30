"""
Topological Road Network Graph Builder.
Converts OpenStreetMap LineString road geometries into a NetworkX graph with metric edge weights.
"""
from typing import Dict, Any, List, Tuple, Set
import networkx as nx
from shapely.geometry import shape, LineString, Point
from src.utils.geo_utils import haversine_distance


class RoadGraphBuilder:
    """
    Constructs a weighted undirected NetworkX graph from OpenStreetMap road features.
    """

    def build_graph(
        self, roads_geojson: Dict[str, Any]
    ) -> Tuple[nx.Graph, Dict[str, Tuple[float, float]]]:
        """
        Builds the graph G = (V, E) where:
        - Nodes represent coordinate intersections / road endpoints.
        - Edges represent road segments with length (meters) and properties.
        """
        graph = nx.Graph()
        node_coords: Dict[str, Tuple[float, float]] = {}

        def get_node_id(lon: float, lat: float) -> str:
            # Round coordinates to ~1 meter precision to snap intersections
            key = f"node_{round(lon, 5)}_{round(lat, 5)}"
            if key not in node_coords:
                node_coords[key] = (lat, lon)
            return key

        for feat in roads_geojson.get("features", []):
            geom = shape(feat["geometry"])
            props = feat.get("properties", {})
            way_id = feat.get("id", "way_unknown")

            if isinstance(geom, LineString):
                coords = list(geom.coords)
                for i in range(len(coords) - 1):
                    lon1, lat1 = coords[i]
                    lon2, lat2 = coords[i + 1]

                    u = get_node_id(lon1, lat1)
                    v = get_node_id(lon2, lat2)

                    # Compute physical distance along segment
                    dist_meters = haversine_distance((lat1, lon1), (lat2, lon2))
                    speed_kph = props.get("speed_kph", 30.0)
                    time_minutes = (dist_meters / 1000.0) / speed_kph * 60.0

                    graph.add_edge(
                        u,
                        v,
                        way_id=way_id,
                        length_meters=dist_meters,
                        time_minutes=time_minutes,
                        highway=props.get("highway", "road"),
                        name=props.get("name", "Unnamed Road"),
                        bridge=props.get("bridge", "no"),
                        is_severed=props.get("is_potentially_affected", False),
                    )

        return graph, node_coords

    def find_nearest_node(
        self, target_coord: Tuple[float, float], node_coords: Dict[str, Tuple[float, float]]
    ) -> str:
        """
        Finds the closest graph node to a target (lat, lon).
        """
        target_lat, target_lon = target_coord
        best_node = None
        min_dist = float("inf")

        for node_id, (n_lat, n_lon) in node_coords.items():
            dist = haversine_distance((target_lat, target_lon), (n_lat, n_lon))
            if dist < min_dist:
                min_dist = dist
                best_node = node_id

        return best_node or ""

