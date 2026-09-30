"""
DEM-Based Downstream Flow-Path Tracer (Bonus Feature).
Given an upstream trigger point (e.g. glacial collapse / avalanche source),
traces downstream valley flow path following topographic gradient.
Label: "Estimated terrain-driven downstream path" (Topographic approximation, not 2D hydrodynamic simulation).
"""
from typing import Dict, Any, List, Tuple, Optional
import numpy as np
from shapely.geometry import Point, LineString, shape
from src.utils.geo_utils import haversine_distance


class DEMFlowTracer:
    """
    Computes topographic steepest descent flow paths across Copernicus WorldDEM-30 grids.
    """

    def trace_flow_path(
        self,
        upstream_coord: Tuple[float, float],
        dem_data: Dict[str, Any],
        settlements_fc: Optional[Dict[str, Any]] = None,
        max_steps: int = 150,
    ) -> Dict[str, Any]:
        """
        Traces steepest downhill gradient from upstream_coord (lat, lon) across DEM elevation matrix.
        Identifies settlements in proximity to the estimated downstream corridor.
        """
        up_lat, up_lon = upstream_coord
        elevation = dem_data["elevation"]
        bbox = dem_data["bbox"]
        min_lon, min_lat, max_lon, max_lat = bbox
        ny, nx = elevation.shape

        # Map geographic coordinate to grid indices
        def coord_to_grid(lat: float, lon: float) -> Tuple[int, int]:
            gx = int((lon - min_lon) / (max_lon - min_lon) * (nx - 1))
            gy = int((max_lat - lat) / (max_lat - min_lat) * (ny - 1))
            return max(0, min(ny - 1, gy)), max(0, min(nx - 1, gx))

        def grid_to_coord(gy: int, gx: int) -> Tuple[float, float]:
            lon = min_lon + (gx / (nx - 1)) * (max_lon - min_lon)
            lat = max_lat - (gy / (ny - 1)) * (max_lat - min_lat)
            return lat, lon

        cur_gy, cur_gx = coord_to_grid(up_lat, up_lon)
        path_coords = [(up_lon, up_lat)]
        visited = set()

        for _ in range(max_steps):
            visited.add((cur_gy, cur_gx))
            cur_elev = elevation[cur_gy, cur_gx]

            # 8-neighborhood search for steepest descent
            best_next = None
            max_drop = 0.0

            for dy in [-1, 0, 1]:
                for dx in [-1, 0, 1]:
                    if dy == 0 and dx == 0:
                        continue
                    ny_idx, nx_idx = cur_gy + dy, cur_gx + dx
                    if 0 <= ny_idx < ny and 0 <= nx_idx < nx:
                        if (ny_idx, nx_idx) not in visited:
                            drop = cur_elev - elevation[ny_idx, nx_idx]
                            # Distance weighting (diagonal vs orthogonal)
                            dist_mult = 1.414 if (dy != 0 and dx != 0) else 1.0
                            drop_rate = drop / dist_mult
                            if drop_rate > max_drop:
                                max_drop = drop_rate
                                best_next = (ny_idx, nx_idx)

            if not best_next or max_drop <= 0.1:
                # Reached local depression / flat valley floor
                break

            cur_gy, cur_gx = best_next
            plat, plon = grid_to_coord(cur_gy, cur_gx)
            path_coords.append((plon, plat))

        flow_line = LineString(path_coords) if len(path_coords) >= 2 else None

        # Identify settlements along flow path corridor (within ~1.5 km)
        exposed_settlements = []
        if settlements_fc and flow_line:
            for feat in settlements_fc.get("features", []):
                pt_geom = shape(feat["geometry"])
                # Approximate distance in km
                dist_km = flow_line.distance(pt_geom) * 105.0
                if dist_km < 1.5:
                    exposed_settlements.append({
                        "name": feat["properties"].get("name", "Settlement"),
                        "distance_to_flow_axis_km": round(dist_km, 2),
                        "estimated_flow_warning": "High exposure along primary drainage axis",
                    })

        return {
            "upstream_point": [up_lon, up_lat],
            "flow_path_geojson": {
                "type": "Feature",
                "properties": {
                    "feature_type": "estimated_downstream_flow_path",
                    "total_points": len(path_coords),
                    "elevation_drop_m": float(elevation[coord_to_grid(up_lat, up_lon)] - elevation[cur_gy, cur_gx]),
                    "label": "Estimated terrain-driven downstream path (Topographic approximation)",
                },
                "geometry": {
                    "type": "LineString",
                    "coordinates": path_coords,
                }
            } if flow_line else None,
            "exposed_settlements_count": len(exposed_settlements),
            "exposed_settlements": exposed_settlements,
            "disclaimer": "This is a terrain-gradient flow estimation, not a 2D hydrodynamic simulation.",
        }
