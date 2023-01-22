import requests
import json
from cache_utils import cached
import time


# Base URL
base_url = "https://api.moovitapp.com/services-app/services/EX/API"

def get_nearby_stops(lat, lon, radius=20, max_stops=10):
    """ Performs a POST request to /GetNearbyObjects with "location" as the body
    """
    # Body
    body = {
        "location": {"lat": lat, "lon": lon},
        "objectTypeFilter": "stop",
        "radiusMeters": radius,
        "maxStops": max_stops,
    }
    # Headers
    headers = {"Content-Type": "application/json"}
    # Perform request
    r = requests.post(f"{base_url}/GetNearbyObjects", data=json.dumps(body), headers=headers)
    # Return result
    return r

lat_carapinheira, lon_carapinheira = 38.935608, -9.311602

stops = get_nearby_stops(lat_carapinheira, lon_carapinheira)

