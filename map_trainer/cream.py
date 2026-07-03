from geopy.distance import geodesic
distance = geodesic(
    (location.lat, location.lng),
    (user_lat, user_lng)
).meters
