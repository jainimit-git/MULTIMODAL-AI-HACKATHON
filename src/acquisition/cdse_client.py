"""
Copernicus Data Space Ecosystem (CDSE) OData Catalogue Client.
Used for discovering Sentinel-1 and Sentinel-2 acquisitions.
Documentation: https://dataspace.copernicus.eu
"""
from typing import Dict, Any, List, Optional, Tuple
import os
import requests
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)


class CDSEClient:
    """
    Client for interacting with the Copernicus Data Space Ecosystem OData API.
    """

    def __init__(
        self,
        base_url: str = "https://catalogue.dataspace.copernicus.eu/odata/v1",
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.client_id = client_id or os.environ.get("COPERNICUS_CLIENT_ID")
        self.client_secret = client_secret or os.environ.get("COPERNICUS_CLIENT_SECRET")
        self._access_token: Optional[str] = None

    def search_products(
        self,
        collection_name: str,
        bbox: List[float],
        start_date: str,
        end_date: str,
        additional_filters: Optional[List[str]] = None,
        top: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        Searches CDSE OData catalogue for products matching AOI and date range.
        bbox format: [min_lon, min_lat, max_lon, max_lat]
        """
        min_lon, min_lat, max_lon, max_lat = bbox
        
        # OData polygon format: POLYGON((min_lon min_lat, max_lon min_lat, ...))
        polygon_wkt = (
            f"POLYGON(({min_lon} {min_lat}, {max_lon} {min_lat}, "
            f"{max_lon} {max_lat}, {min_lon} {max_lat}, {min_lon} {min_lat}))"
        )
        
        filter_parts = [
            f"Collection/Name eq '{collection_name}'",
            f"OData.CSC.Intersects(area=geography'SRID=4326;{polygon_wkt}')",
            f"ContentDate/Start ge {start_date}T00:00:00.000Z",
            f"ContentDate/Start le {end_date}T23:59:59.999Z",
        ]
        
        if additional_filters:
            filter_parts.extend(additional_filters)

        filter_query = " and ".join(filter_parts)
        endpoint = f"{self.base_url}/Products"
        params = {
            "$filter": filter_query,
            "$top": top,
            "$orderby": "ContentDate/Start desc",
        }

        try:
            response = requests.get(endpoint, params=params, timeout=15)
            if response.status_code == 200:
                data = response.json()
                return data.get("value", [])
            else:
                logger.warning(
                    f"CDSE API returned status {response.status_code}: {response.text[:200]}"
                )
                return []
        except Exception as e:
            logger.error(f"Failed to query CDSE API: {e}")
            return []

