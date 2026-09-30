"""
Unit tests for topological road network graph routing and cut-off settlement analysis.
"""
from src.network.road_graph import RoadGraphBuilder
from src.network.cutoff_analyzer import CutOffAnalyzer
from src.acquisition.osm_client import OSMPreEventClient
from src.gis.infrastructure_analyzer import InfrastructureAnalyzer


def test_road_network_routing_and_cutoff():
    osm_client = OSMPreEventClient()
    bbox = [85.15, 27.85, 85.45, 28.25]
    infra = osm_client.extract_pre_event_infrastructure(bbox)

    # Simulate flood severing the main highway and feeder roads to Village B and C
    mid_lon = 85.30
    mid_lat = 28.05
    flood_fc = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [mid_lon - 0.02, mid_lat - 0.02],
                        [mid_lon + 0.04, mid_lat - 0.02],
                        [mid_lon + 0.04, mid_lat + 0.03],
                        [mid_lon - 0.02, mid_lat + 0.03],
                        [mid_lon - 0.02, mid_lat - 0.02],
                    ]]
                }
            }
        ]
    }

    gis_analyzer = InfrastructureAnalyzer()
    gis_res = gis_analyzer.analyze_exposure(flood_fc, infra)

    cutoff_analyzer = CutOffAnalyzer()
    cutoff_res = cutoff_analyzer.analyze_connectivity(
        gis_res["annotated_roads"], infra["settlements"]
    )

    summary = cutoff_res["summary"]
    assert summary["total_settlements"] >= 4
    # Village B and C should be isolated
    assert summary["cut_off_settlements_count"] >= 1
    
    # Check that individual settlement states are computed correctly
    settlements = cutoff_res["settlements"]
    cut_off_names = [s["name"] for s in settlements if s["is_cut_off"]]
    assert any("Village" in name for name in cut_off_names)
