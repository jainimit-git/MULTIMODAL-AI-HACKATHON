"""
Unit tests for satellite discovery, same-orbit track matching, pre-event OSM extraction, and DEM loading.
"""
from src.acquisition.s1_finder import Sentinel1Finder
from src.acquisition.s2_finder import Sentinel2Finder
from src.acquisition.osm_client import OSMPreEventClient
from src.acquisition.dem_loader import DEMLoader


def test_sentinel1_same_orbit_pairing():
    finder = Sentinel1Finder()
    bbox = [85.15, 27.85, 85.45, 28.25]
    result = finder.find_orbit_matched_pair(
        bbox=bbox,
        event_date="2026-08-26",
        preferred_relative_orbit=19
    )

    assert result is not None
    assert "pre_event" in result
    assert "post_event" in result
    assert result["relative_orbit"] == 19
    assert result["pre_event"]["relative_orbit"] == result["post_event"]["relative_orbit"]
    assert "Contains modified Copernicus Sentinel data 2026." in result["attribution"]


def test_sentinel2_cloud_filtering():
    finder = Sentinel2Finder()
    bbox = [85.15, 27.85, 85.45, 28.25]
    result = finder.find_cloud_filtered_scenes(
        bbox=bbox,
        event_date="2026-08-26",
        max_cloud_cover_percent=30.0
    )

    assert result is not None
    assert "pre_event" in result
    assert "post_event" in result
    assert result["cloud_cover_post_percent"] <= 30.0
    assert "Contains modified Copernicus Sentinel data 2026." in result["attribution"]


def test_osm_pre_event_snapshot_compliance():
    client = OSMPreEventClient(snapshot_date="2026-07-27T00:00:00Z")
    bbox = [85.15, 27.85, 85.45, 28.25]
    infra = client.extract_pre_event_infrastructure(bbox)

    assert "roads" in infra
    assert "settlements" in infra
    assert "buildings" in infra
    assert infra["snapshot_timestamp"] <= "2026-07-27T00:00:00Z"
    assert "© OpenStreetMap contributors." in infra["attribution"]

    # Verify road network features
    road_features = infra["roads"]["features"]
    assert len(road_features) >= 4
    bridge_found = any(f["properties"].get("bridge") == "yes" for f in road_features)
    assert bridge_found is True


def test_dem_loader_and_slope():
    loader = DEMLoader(resolution_meters=30)
    bbox = [85.15, 27.85, 85.45, 28.25]
    dem_data = loader.load_elevation_grid(bbox, grid_shape=(64, 64))

    assert "elevation" in dem_data
    assert "slope_degrees" in dem_data
    assert "steep_slope_mask" in dem_data
    assert dem_data["elevation"].shape == (64, 64)
    assert dem_data["min_elevation_m"] >= 500.0
    assert "Copernicus WorldDEM-30" in dem_data["attribution"]

