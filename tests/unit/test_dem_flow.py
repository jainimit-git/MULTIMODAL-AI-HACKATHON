"""
Unit tests for DEM-based downstream flow path tracing.
"""
from src.dem.flow_tracer import DEMFlowTracer
from src.acquisition.dem_loader import DEMLoader
from src.acquisition.osm_client import OSMPreEventClient


def test_dem_flow_tracer():
    dem_loader = DEMLoader()
    bbox = [85.15, 27.85, 85.45, 28.25]
    dem_data = dem_loader.load_elevation_grid(bbox, grid_shape=(64, 64))

    osm_client = OSMPreEventClient()
    infra = osm_client.extract_pre_event_infrastructure(bbox)

    tracer = DEMFlowTracer()
    # Upstream high altitude starting point in north valley
    upstream_coord = (28.20, 85.32)
    res = tracer.trace_flow_path(upstream_coord, dem_data, infra["settlements"])

    assert "flow_path_geojson" in res
    assert res["flow_path_geojson"] is not None
    assert res["flow_path_geojson"]["geometry"]["type"] == "LineString"
    assert len(res["flow_path_geojson"]["geometry"]["coordinates"]) >= 2
    assert "Estimated terrain-driven downstream path" in res["disclaimer"] or "terrain-gradient" in res["disclaimer"]

