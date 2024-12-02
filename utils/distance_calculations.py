import math

def calculate_distance(lat1, lon1, lat2, lon2):
    """
    Calculates the great-circle distance between two points using the formula from Appendix C.
    Inputs are in decimal degrees.
    """
    # Radius of Earth in kilometers
    R = 6371

    # Convert degrees to radians
    lat1, lon1 = math.radians(lat1), math.radians(lon1)
    lat2, lon2 = math.radians(lat2), math.radians(lon2)

    # Compute the differences
    delta_lat = lat2 - lat1
    delta_lon = lon2 - lon1

    # Apply the formula
    a = math.sin(delta_lat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(delta_lon / 2)**2
    delta_sigma = 2 * math.asin(math.sqrt(a))
    distance = R * delta_sigma

    return distance


