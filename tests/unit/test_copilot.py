"""
Unit tests for grounded bilingual disaster copilot.
"""
from src.copilot.copilot_engine import DisasterCopilot


def test_copilot_english_and_nepali():
    dummy_analysis = {
        "flood_metrics": {"total_affected_area_km2": 38.2},
        "infrastructure_metrics": {"total_bridges": 5, "affected_bridges": 2},
        "network_metrics": {
            "destination_hospital": "Trishuli District Hospital",
            "settlements": [
                {"name": "Village B", "population": 620, "is_cut_off": True},
                {"name": "Village A", "population": 850, "is_cut_off": False},
            ],
        },
        "satellite_metadata": {
            "sentinel1": {"relative_orbit": 19, "pre_event_date": "2026-08-16", "post_event_date": "2026-08-28"}
        },
    }

    copilot = DisasterCopilot(dummy_analysis)

    # 1. English cut-off query
    res_en = copilot.answer_query("Which villages are cut off from the hospital?")
    assert res_en["language"] == "en"
    assert "Village B" in res_en["answer"]

    # 2. Nepali cut-off query
    res_ne = copilot.answer_query("कुन कुन गाउँहरू सम्पर्कविहीन भएका छन्?")
    assert res_ne["language"] == "ne"
    assert "Village B" in res_ne["answer"]

    # 3. Bridges query
    res_b = copilot.answer_query("How many bridges are potentially affected?")
    assert "2 out of 5" in res_b["answer"]

    # 4. Out of scope query returns ungrounded fallback
    res_unk = copilot.answer_query("What is the weather tomorrow in Paris?")
    assert "Insufficient information" in res_unk["answer"]

