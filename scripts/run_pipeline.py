"""
AEROSIS Master Pipeline Orchestrator & CLI Runner.
Executes end-to-end multimodal disaster intelligence analysis from raw permitted data.
Supports both predefined event configs (e.g. Trishuli 2026) and Judge Live Evaluation mode.
"""
import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.config_loader import load_config
from src.utils.geo_utils import validate_bbox
from src.acquisition.s1_finder import Sentinel1Finder
from src.acquisition.s2_finder import Sentinel2Finder
from src.acquisition.osm_client import OSMPreEventClient
from src.acquisition.dem_loader import DEMLoader
from src.segmentation.model_runner import MultimodalFloodPipeline
from src.gis.infrastructure_analyzer import InfrastructureAnalyzer
from src.network.cutoff_analyzer import CutOffAnalyzer
from src.dem.flow_tracer import DEMFlowTracer
from src.reporting.sitrep_generator import SitRepGenerator
from src.validation.emsr927_validator import EMSR927Validator


def run_full_pipeline(
    bbox: List[float],
    event_date: str,
    event_name: str = "Disaster Assessment Event",
    country: str = "Nepal",
    region: str = "Alpine Valley",
    output_dir: str = "data/outputs",
    is_trishuli_case_study: bool = False,
) -> Dict[str, Any]:
    """
    Executes all 10 pipeline steps end-to-end.
    """
    validate_bbox(bbox)
    os.makedirs(output_dir, exist_ok=True)

    print("=" * 70)
    print("AEROSIS - MULTIMODAL SATELLITE DISASTER INTELLIGENCE SYSTEM")
    print(f"Event: {event_name} | Date: {event_date}")
    print(f"AOI Bounding Box: {bbox}")
    print("=" * 70)

    # 1. Satellite Discovery
    print("\n[1/7] Discovering permitted satellite imagery (Copernicus CDSE)...")
    s1_finder = Sentinel1Finder()
    s1_pair = s1_finder.find_orbit_matched_pair(bbox, event_date)
    print(f"  [OK] Sentinel-1 Matched Pair: Track R{s1_pair['relative_orbit']} ({s1_pair['orbit_direction']})")
    print(f"       Pre-event: {s1_pair['pre_event']['acquisition_date_str']} | Post-event: {s1_pair['post_event']['acquisition_date_str']}")

    s2_finder = Sentinel2Finder()
    s2_scenes = s2_finder.find_cloud_filtered_scenes(bbox, event_date)
    print(f"  [OK] Sentinel-2 Optical: Cloud cover {s2_scenes['cloud_cover_post_percent']}%")

    # 2. Elevation & Topography
    print("\n[2/7] Loading Copernicus WorldDEM-30 elevation & slope grid...")
    dem_loader = DEMLoader()
    dem_data = dem_loader.load_elevation_grid(bbox, grid_shape=(64, 64))
    print(f"  [OK] Elevation range: {int(dem_data['min_elevation_m'])}m - {int(dem_data['max_elevation_m'])}m")

    # 3. Pre-event OpenStreetMap Baseline
    print("\n[3/7] Querying pre-event OpenStreetMap baseline (ohsome adapter)...")
    osm_client = OSMPreEventClient()
    osm_infra = osm_client.extract_pre_event_infrastructure(bbox)
    print(f"  [OK] Pre-event infrastructure loaded: {len(osm_infra['roads']['features'])} road segments, "
          f"{len(osm_infra['settlements']['features'])} settlements, {len(osm_infra['buildings']['features'])} building clusters.")

    # 4. Multimodal AI Flood/Debris Segmentation
    print("\n[4/7] Running Multimodal AI Flood & Debris Segmentation (UNet + SAR Change)...")
    segmentor = MultimodalFloodPipeline()
    seg_result = segmentor.run_segmentation(
        s1_data=s1_pair,
        s2_data=s2_scenes,
        dem_data=dem_data,
        bbox=bbox,
        grid_shape=(64, 64)
    )
    flood_fc = seg_result["geojson_polygons"]
    print(f"  [OK] Total estimated affected area: {seg_result['total_affected_area_km2']} km2 "
          f"({len(flood_fc['features'])} flood polygons)")

    # 5. Infrastructure Spatial Exposure
    print("\n[5/7] Analyzing spatial infrastructure exposure & bridge severances...")
    gis_analyzer = InfrastructureAnalyzer()
    gis_result = gis_analyzer.analyze_exposure(flood_fc, osm_infra)
    gis_summary = gis_result["summary"]
    print(f"  [OK] Road impact: {gis_summary['affected_roads_km']} km affected ({gis_summary['percent_roads_affected']}%)")
    print(f"  [OK] Bridge impact: {gis_summary['affected_bridges']} of {gis_summary['total_bridges']} bridges potentially disrupted")
    print(f"  [OK] Building impact: {gis_summary['affected_buildings']} building structures exposed")

    # 6. Topological Road Graph Routing & Cut-off Village Analysis
    print("\n[6/7] Computing topological road network shortest path reachability (NetworkX)...")
    cutoff_analyzer = CutOffAnalyzer()
    cutoff_result = cutoff_analyzer.analyze_connectivity(
        gis_result["annotated_roads"], osm_infra["settlements"]
    )
    net_summary = cutoff_result["summary"]
    print(f"  [OK] Target medical destination: {net_summary['destination_hospital']}")
    print(f"  [OK] Cut-off settlements: {net_summary['cut_off_settlements_count']} villages isolated "
          f"({net_summary['isolated_population']} population)")
    for s in cutoff_result["settlements"]:
        status_icon = "[CUT OFF]" if s["is_cut_off"] else "[CONNECTED]"
        print(f"       - {s['name']}: {status_icon} (Pre: {s['pre_event_distance_km']}km, Post: {s['post_event_distance_km']}km)")

    # Bonus: DEM Downstream Flow Path
    print("\n[*] Bonus: Tracing estimated downstream terrain flow path...")
    dem_tracer = DEMFlowTracer()
    mid_lon = (bbox[0] + bbox[2]) / 2.0
    max_lat = bbox[3]
    flow_result = dem_tracer.trace_flow_path((max_lat - 0.02, mid_lon + 0.02), dem_data, osm_infra["settlements"])
    print(f"  [OK] Flow path generated with {flow_result['exposed_settlements_count']} settlements along descent corridor.")

    # 7. Assemble Master JSON & Generate Situation Report
    print("\n[7/7] Synthesizing Situation Report and analysis_result.json...")
    master_result = {
        "event": {
            "name": event_name,
            "country": country,
            "region": region,
            "event_date": event_date,
        },
        "aoi": {
            "bbox": bbox,
            "center": [(bbox[0] + bbox[2]) / 2.0, (bbox[1] + bbox[3]) / 2.0],
        },
        "satellite_metadata": {
            "sentinel1": {
                "pre_event_date": s1_pair["pre_event"]["acquisition_date_str"],
                "post_event_date": s1_pair["post_event"]["acquisition_date_str"],
                "relative_orbit": s1_pair["relative_orbit"],
                "orbit_direction": s1_pair["orbit_direction"],
                "temporal_separation_days": s1_pair["temporal_separation_days"],
            },
            "sentinel2": {
                "cloud_cover_percent": s2_scenes["cloud_cover_post_percent"],
                "pre_event_date": s2_scenes["pre_event"]["acquisition_date_str"],
                "post_event_date": s2_scenes["post_event"]["acquisition_date_str"],
            },
        },
        "flood_metrics": {
            "total_affected_area_km2": seg_result["total_affected_area_km2"],
            "flooded_pixel_count": seg_result["flooded_pixel_count"],
        },
        "infrastructure_metrics": gis_summary,
        "network_metrics": cutoff_result,
        "dem_flow_metrics": flow_result,
        "geojson_layers": {
            "flood_polygons": flood_fc,
            "annotated_roads": gis_result["annotated_roads"],
            "settlements": cutoff_result["settlements_geojson"],
            "flow_path": flow_result.get("flow_path_geojson"),
        },
        "attributions": {
            "copernicus_sentinel": "Contains modified Copernicus Sentinel data 2026.",
            "copernicus_dem": "Produced using Copernicus WorldDEM-30 © DLR e.V. 2010–2014 and © Airbus Defence and Space GmbH 2014–2018 provided under COPERNICUS by the European Union and ESA; all rights reserved.",
            "osm": "© OpenStreetMap contributors.",
        }
    }

    # Optional Post-Hoc Validation for Trishuli Benchmark
    if is_trishuli_case_study or "trishuli" in event_name.lower():
        print("\n[VALIDATION] Running post-hoc benchmark evaluation against Copernicus EMS EMSR927...")
        validator = EMSR927Validator()
        val_result = validator.evaluate_trishuli_result(flood_fc, bbox)
        master_result["validation_benchmark"] = val_result
        print(f"  [OK] EMSR927 Validation Benchmark -> IoU: {val_result['metrics']['intersection_over_union_iou']}, "
              f"Dice/F1: {val_result['metrics']['dice_f1_score']}, Precision: {val_result['metrics']['precision']}, Recall: {val_result['metrics']['recall']}")

    # Generate SitRep
    sitrep_gen = SitRepGenerator()
    sitrep = sitrep_gen.generate_report(master_result)
    master_result["situation_report_md"] = sitrep["markdown_report"]

    # Write output files
    json_path = Path(output_dir) / "analysis_result.json"
    sitrep_path = Path(output_dir) / "situation_report.md"

    serializable_dict = json.loads(json.dumps(master_result, default=str))

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(serializable_dict, f, indent=2)

    with open(sitrep_path, "w", encoding="utf-8") as f:
        f.write(sitrep["markdown_report"])

    print(f"\n[DONE] Analysis completed successfully!")
    print(f"  Outputs written to:")
    print(f"  - {json_path}")
    print(f"  - {sitrep_path}")
    print("=" * 70)

    return serializable_dict


def main():
    parser = argparse.ArgumentParser(description="AEROSIS Multimodal Satellite Disaster Pipeline")
    parser.add_argument("--config", type=str, help="Path to YAML event configuration")
    parser.add_argument("--aoi", type=str, help="AOI bbox as min_lon,min_lat,max_lon,max_lat")
    parser.add_argument("--date", type=str, help="Event date as YYYY-MM-DD")
    parser.add_argument("--output-dir", type=str, default="data/outputs", help="Output directory")

    args = parser.parse_args()

    if args.config:
        cfg = load_config(args.config)
        bbox = cfg.get("aoi", {}).get("bbox", [85.15, 27.85, 85.45, 28.25])
        event_date = cfg.get("event", {}).get("event_date", "2026-08-26")
        event_name = cfg.get("event", {}).get("name", "August 2026 Trishuli Debris Flood")
        country = cfg.get("event", {}).get("country", "Nepal")
        region = cfg.get("event", {}).get("region", "Trishuli Corridor")
        is_trishuli = "trishuli" in args.config.lower()
    elif args.aoi and args.date:
        coords = [float(x.strip()) for x in args.aoi.split(",")]
        bbox = coords
        event_date = args.date
        event_name = f"Live Judge Evaluation ({event_date})"
        country = "Nepal / Global"
        region = "User AOI"
        is_trishuli = False
    else:
        cfg = load_config("config/trishuli.yaml")
        bbox = cfg.get("aoi", {}).get("bbox", [85.15, 27.85, 85.45, 28.25])
        event_date = cfg.get("event", {}).get("event_date", "2026-08-26")
        event_name = cfg.get("event", {}).get("name", "August 2026 Trishuli Debris Flood")
        country = cfg.get("event", {}).get("country", "Nepal")
        region = cfg.get("event", {}).get("region", "Trishuli Corridor")
        is_trishuli = True

    run_full_pipeline(
        bbox=bbox,
        event_date=event_date,
        event_name=event_name,
        country=country,
        region=region,
        output_dir=args.output_dir,
        is_trishuli_case_study=is_trishuli,
    )


if __name__ == "__main__":
    main()

