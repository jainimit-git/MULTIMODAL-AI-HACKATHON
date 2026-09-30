"""
Unit tests for geospatial mathematics, bounding box validation, and metric calculations.
"""
import pytest
import numpy as np
from src.utils.geo_utils import (
    validate_bbox,
    bbox_to_polygon,
    haversine_distance,
    calculate_iou,
    calculate_dice_f1,
)


def test_validate_bbox_valid():
    bbox = [85.15, 27.85, 85.45, 28.25]
    assert validate_bbox(bbox) is True


def test_validate_bbox_invalid_length():
    with pytest.raises(ValueError, match="must have 4 elements"):
        validate_bbox([85.15, 27.85, 85.45])


def test_validate_bbox_inverted_coords():
    with pytest.raises(ValueError, match="strictly less than"):
        validate_bbox([85.45, 27.85, 85.15, 28.25])


def test_bbox_to_polygon():
    bbox = [85.15, 27.85, 85.45, 28.25]
    poly = bbox_to_polygon(bbox)
    assert poly.is_valid
    assert poly.bounds == (85.15, 27.85, 85.45, 28.25)
    assert poly.area > 0


def test_haversine_distance():
    coord1 = (27.925, 85.185)
    coord2 = (28.112, 85.297)
    dist = haversine_distance(coord1, coord2)
    assert 20000 < dist < 30000


def test_calculate_iou_and_dice():
    pred = np.array([
        [1, 1, 0],
        [0, 1, 0],
        [0, 0, 0]
    ])
    true = np.array([
        [0, 1, 1],
        [0, 1, 0],
        [0, 0, 0]
    ])
    iou = calculate_iou(pred, true)
    assert iou == pytest.approx(0.5)

    dice = calculate_dice_f1(pred, true)
    assert dice == pytest.approx(2.0 / 3.0)


def test_calculate_iou_empty_masks():
    empty_pred = np.zeros((5, 5))
    empty_true = np.zeros((5, 5))
    assert calculate_iou(empty_pred, empty_true) == 1.0
    assert calculate_dice_f1(empty_pred, empty_true) == 1.0
