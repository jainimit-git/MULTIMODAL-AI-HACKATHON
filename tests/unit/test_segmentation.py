"""
Unit tests for Multimodal AI segmentation model, vectorization, and pipeline runner.
"""
import numpy as np
import torch
from src.segmentation.multimodal_unet import MultimodalFloodUNet
from src.segmentation.vectorizer import MaskVectorizer
from src.segmentation.model_runner import MultimodalFloodPipeline


def test_multimodal_unet_forward_pass():
    model = MultimodalFloodUNet(in_channels=6, num_classes=2)
    model.eval()
    # Batch=1, Channels=6, Height=32, Width=32
    x = torch.randn(1, 6, 32, 32)
    with torch.no_grad():
        out = model(x)
    assert out.shape == (1, 2, 32, 32)


def test_mask_vectorizer():
    vectorizer = MaskVectorizer(min_pixel_area=4)
    raw_mask = np.zeros((20, 20), dtype=np.uint8)
    # Create a 4x4 block (16 pixels)
    raw_mask[5:9, 5:9] = 1
    # Create isolated 1-pixel noise
    raw_mask[0, 0] = 1

    cleaned = vectorizer.clean_mask(raw_mask)
    assert cleaned[0, 0] == 0  # Noise removed
    assert cleaned[5:9, 5:9].sum() > 0

    bbox = [85.15, 27.85, 85.45, 28.25]
    geojson = vectorizer.vectorize_to_geojson(cleaned, bbox=bbox)
    assert geojson["type"] == "FeatureCollection"
    assert len(geojson["features"]) >= 1
    assert "geometry" in geojson["features"][0]


def test_multimodal_pipeline_runner():
    pipeline = MultimodalFloodPipeline()
    bbox = [85.15, 27.85, 85.45, 28.25]
    dem_data = {
        "elevation": np.ones((32, 32)) * 1000.0,
        "slope_degrees": np.ones((32, 32)) * 12.0,
        "steep_slope_mask": np.zeros((32, 32), dtype=np.uint8),
    }

    result = pipeline.run_segmentation(
        s1_data={},
        s2_data={},
        dem_data=dem_data,
        bbox=bbox,
        grid_shape=(32, 32)
    )

    assert "binary_mask" in result
    assert "geojson_polygons" in result
    assert "total_affected_area_km2" in result
    assert result["total_affected_area_km2"] >= 0
    assert "Contains modified Copernicus Sentinel data 2026." in result["attribution"]

