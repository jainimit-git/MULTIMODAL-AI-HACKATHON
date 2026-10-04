"""
Unit tests for deterministic Situation Report (SitRep) generator.
"""
from src.reporting.sitrep_generator import SitRepGenerator


def test_sitrep_generator():
    generator = SitRepGenerator()
    dummy_analysis = {
        "event": {"name": "August 2026 Trishuli Flood", "country": "Nepal", "event_date": "2026-08-26"},
        "satellite_metadata": {
            "sentinel1": {"relative_orbit": 19, "pre_event_date": "2026-08-16", "post_event_date": "2026-08-28"},
            "sentinel2": {"cloud_cover_percent": 12.5},
        },
        "flood_metrics": {"total_affected_area_km2": 42.5},
        "infrastructure_metrics": {
            "total_roads_km": 120.0,
            "affected_roads_km": 18.5,
            "percent_roads_affected": 15.4,
            "total_bridges": 4,
            "affected_bridges": 2,
            "affected_buildings": 28,
        },
        "network_metrics": {
            "destination_hospital": "Trishuli District Hospital",
            "isolated_population": 1400,
            "settlements": [
                {"name": "Village B", "is_cut_off": True},
                {"name": "Village A", "is_cut_off": False},
            ],
        },
    }

    report = generator.generate_report(dummy_analysis)
    assert "markdown_report" in report
    md = report["markdown_report"]
    assert "DISASTER SITUATION REPORT" in md
    assert "42.5 km²" in md
    assert "Trishuli District Hospital" in md
    assert "Village B" in md
    assert "Contains modified Copernicus Sentinel data 2026." in md

