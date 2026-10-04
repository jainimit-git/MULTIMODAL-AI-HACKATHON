"""
Unit tests for EMSR927 post-hoc validation benchmark.
"""
from src.validation.emsr927_validator import EMSR927Validator


def test_emsr927_validator():
    validator = EMSR927Validator()
    bbox = [85.15, 27.85, 85.45, 28.25]
    predicted_geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [85.25, 27.90],
                        [85.35, 27.90],
                        [85.35, 28.15],
                        [85.25, 28.15],
                        [85.25, 27.90],
                    ]]
                }
            }
        ]
    }

    val = validator.evaluate_trishuli_result(predicted_geojson, bbox=bbox, grid_shape=(32, 32))
    assert "metrics" in val
    metrics = val["metrics"]
    assert "intersection_over_union_iou" in metrics
    assert "dice_f1_score" in metrics
    assert metrics["intersection_over_union_iou"] >= 0.0
    assert "European Union, Copernicus Emergency Management Service data (EMSR927)" in val["attribution"]

