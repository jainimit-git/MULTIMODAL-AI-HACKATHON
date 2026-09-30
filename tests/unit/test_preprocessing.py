"""
Unit tests for SAR radiometric calibration and optical spectral indices.
"""
import numpy as np
from src.preprocessing.sar_preprocessor import SARPreprocessor
from src.preprocessing.optical_preprocessor import OpticalPreprocessor
from src.change_detection.sar_change import SARChangeDetector


def test_sar_preprocessor_calibration():
    prep = SARPreprocessor(filter_window_size=3)
    raw = np.array([
        [0.01, 0.02, 0.01],
        [0.02, 0.05, 0.02],
        [0.01, 0.02, 0.01]
    ])
    sigma0_db = prep.calibrate_and_filter(raw, apply_speckle_filter=True)
    assert sigma0_db.shape == raw.shape
    # -30 dB to 0 dB is typical SAR backscatter range
    assert np.all(sigma0_db < 0.0)
    assert np.all(sigma0_db > -40.0)


def test_optical_preprocessor_mndwi():
    prep = OpticalPreprocessor()
    green = np.array([[0.3, 0.1], [0.4, 0.1]])
    swir = np.array([[0.05, 0.4], [0.02, 0.5]])
    red = np.array([[0.1, 0.2], [0.1, 0.2]])
    nir = np.array([[0.1, 0.5], [0.08, 0.6]])

    res = prep.compute_indices(green, red, nir, swir)
    assert "mndwi" in res
    assert "water_mask" in res
    # Water pixel (high green, low swir) has high MNDWI
    assert res["mndwi"][0, 0] > 0.5
    assert res["water_mask"][0, 0] == 1
    # Non-water pixel has negative MNDWI
    assert res["mndwi"][0, 1] < 0.0
    assert res["water_mask"][0, 1] == 0


def test_sar_change_detector():
    detector = SARChangeDetector(water_drop_threshold_db=-2.5)
    pre_vv = np.array([[-12.0, -14.0], [-10.0, -11.0]])
    post_vv = np.array([[-18.0, -14.0], [-10.0, -11.0]])  # (0,0) dropped by 6dB (inundated)
    pre_vh = np.array([[-20.0, -22.0], [-18.0, -19.0]])
    post_vh = np.array([[-26.0, -22.0], [-18.0, -19.0]])

    res = detector.detect_change(pre_vv, pre_vh, post_vv, post_vh)
    assert res["flood_debris_mask"][0, 0] == 1
    assert res["flood_debris_mask"][0, 1] == 0

