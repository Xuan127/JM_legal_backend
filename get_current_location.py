import requests
from geopy.geocoders import Nominatim

def get_current_location():
    """
    Returns the current location as a tuple (state, county) based on IP geolocation.
    This function works best for U.S. locations.
    """
    try:
        # Get latitude and longitude based on your public IP address.
        ip_api_url = "http://ip-api.com/json/"
        response = requests.get(ip_api_url)
        if response.status_code != 200:
            raise Exception("IP geolocation request failed.")
        
        data = response.json()
        lat = data.get("lat")
        lon = data.get("lon")
        if lat is None or lon is None:
            raise Exception("Latitude or Longitude not found in the response.")
        
        # Reverse geocode to get detailed address information.
        geolocator = Nominatim(user_agent="location_app")
        location = geolocator.reverse(f"{lat}, {lon}", language="en")
        if not location:
            raise Exception("Reverse geocoding failed to retrieve location data.")
        
        address = location.raw.get("address", {})
        state = address.get("state", "State not found")
        county = address.get("county", "County not found")
        state = state.lower().replace("state", "").strip().title()
        county = county.lower().replace("county", "").strip().title()
        return state, county

    except Exception as e:
        print(f"An error occurred: {e}")
        return None, None

if __name__ == "__main__":
    state, county = get_current_location()
    if state and county:
        print(f"Current Location: {state}, {county}")
    else:
        print("Could not determine the current location.")
