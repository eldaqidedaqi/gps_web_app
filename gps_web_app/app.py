from flask import Flask, render_template, request, jsonify
import math
import folium
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import os
import time

app = Flask(__name__)

# Configurar geocodificador (offline con caché local)
geolocator = Nominatim(user_agent="gps_web_app", timeout=10)

# Haversine formula to calculate distance between two lat/lon points
def haversine(coord1, coord2):
    R = 6371  # Radius of the Earth in km
    lat1, lon1 = math.radians(coord1[0]), math.radians(coord1[1])
    lat2, lon2 = math.radians(coord2[0]), math.radians(coord2[1])
    
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    distance = R * c  # Distance in km
    return round(distance, 2)

# Triangulation function - Weighted centroid method
def triangulate_position(p1, p2, p3, d1, d2, d3):
    """
    Triangulate position using three reference points and distances.
    Uses weighted centroid method based on inverse distances.
    """
    # Avoid division by zero
    if d1 == 0 or d2 == 0 or d3 == 0:
        d1 = max(d1, 0.001)
        d2 = max(d2, 0.001)
        d3 = max(d3, 0.001)
    
    # Weight by inverse distance
    weights = [1/d1, 1/d2, 1/d3]
    total_weight = sum(weights)
    
    lat = (p1[0] * weights[0] + p2[0] * weights[1] + p3[0] * weights[2]) / total_weight
    lon = (p1[1] * weights[0] + p2[1] * weights[1] + p3[1] * weights[2]) / total_weight
    
    return round(lat, 6), round(lon, 6)

# Geocodify location using Geopy
def geocode_location(location_name):
    """
    Convert location name to coordinates using Geopy/Nominatim.
    Returns tuple (lat, lon) or None if not found.
    """
    try:
        location = geolocator.geocode(location_name)
        if location:
            return location.latitude, location.longitude
        return None
    except (GeocoderTimedOut, GeocoderServiceError) as e:
        print(f"Geocoding error: {e}")
        return None

# Create map with offline tiles
def create_map(lat, lon, zoom=12, location_name="Location"):
    """
    Create a folium map with OpenStreetMap tiles (cached by browser).
    """
    map_obj = folium.Map(
        location=[lat, lon],
        zoom_start=zoom,
        tiles='OpenStreetMap'  # Uses OSM tiles (cached by Folium)
    )
    
    # Add marker with popup
    folium.Marker(
        [lat, lon],
        popup=f"<b>{location_name}</b><br>Lat: {lat:.4f}<br>Lon: {lon:.4f}",
        tooltip=location_name
    ).add_to(map_obj)
    
    # Add circle for reference
    folium.Circle(
        [lat, lon],
        radius=500,
        color='blue',
        fill=True,
        fillColor='blue',
        fillOpacity=0.2
    ).add_to(map_obj)
    
    return map_obj

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        search_query = request.form.get('location', '').strip()
        
        if not search_query:
            return render_template('index.html', error='Please enter a location')
        
        # Geocodify the location
        coords = geocode_location(search_query)
        
        if coords is None:
            return render_template('index.html', error=f'Location "{search_query}" not found. Try coordinates or a known place.')
        
        lat, lon = coords
        
        # Create map
        map_obj = create_map(lat, lon, location_name=search_query)
        map_obj.save('templates/map.html')
        
        return render_template('map.html', location=search_query, lat=lat, lon=lon)
    
    return render_template('index.html')

@app.route('/distance', methods=['GET', 'POST'])
def calculate_distance():
    if request.method == 'POST':
        try:
            lat1 = float(request.form.get('lat1', 0))
            lon1 = float(request.form.get('lon1', 0))
            lat2 = float(request.form.get('lat2', 0))
            lon2 = float(request.form.get('lon2', 0))
            
            if lat1 == 0 and lon1 == 0 and lat2 == 0 and lon2 == 0:
                return render_template('distance_form.html', error='Please enter valid coordinates')
            
            distance = haversine((lat1, lon1), (lat2, lon2))
            
            # Create map with both points
            map_obj = folium.Map(
                location=[(lat1 + lat2) / 2, (lon1 + lon2) / 2],
                zoom_start=12,
                tiles='OpenStreetMap'
            )
            
            # Add markers
            folium.Marker([lat1, lon1], popup="Point 1", tooltip="Point 1", icon=folium.Icon(color='blue')).add_to(map_obj)
            folium.Marker([lat2, lon2], popup="Point 2", tooltip="Point 2", icon=folium.Icon(color='red')).add_to(map_obj)
            
            # Draw line between points
            folium.PolyLine(
                locations=[[lat1, lon1], [lat2, lon2]],
                color='green',
                weight=3,
                opacity=0.8
            ).add_to(map_obj)
            
            map_obj.save('templates/distance_map.html')
            
            return render_template('distance_result.html', 
                                 distance=distance, 
                                 lat1=lat1, 
                                 lon1=lon1, 
                                 lat2=lat2, 
                                 lon2=lon2)
        except ValueError:
            return render_template('distance_form.html', error='Please enter valid numbers for coordinates')
    
    return render_template('distance_form.html')

@app.route('/triangulate', methods=['GET', 'POST'])
def triangulate():
    if request.method == 'POST':
        try:
            lat1 = float(request.form.get('lat1', 0))
            lon1 = float(request.form.get('lon1', 0))
            dist1 = float(request.form.get('dist1', 0))
            
            lat2 = float(request.form.get('lat2', 0))
            lon2 = float(request.form.get('lon2', 0))
            dist2 = float(request.form.get('dist2', 0))
            
            lat3 = float(request.form.get('lat3', 0))
            lon3 = float(request.form.get('lon3', 0))
            dist3 = float(request.form.get('dist3', 0))
            
            if (lat1 == 0 and lon1 == 0) or (lat2 == 0 and lon2 == 0) or (lat3 == 0 and lon3 == 0):
                return render_template('triangulation_form.html', error='Please enter all reference points')
            
            if dist1 <= 0 or dist2 <= 0 or dist3 <= 0:
                return render_template('triangulation_form.html', error='Distances must be greater than 0')
            
            result_lat, result_lon = triangulate_position(
                (lat1, lon1), (lat2, lon2), (lat3, lon3),
                dist1, dist2, dist3
            )
            
            # Create map with reference points and result
            map_obj = folium.Map(
                location=[result_lat, result_lon],
                zoom_start=12,
                tiles='OpenStreetMap'
            )
            
            # Add reference points
            folium.Marker([lat1, lon1], popup=f"Ref 1 (dist: {dist1}km)", 
                         tooltip="Reference Point 1", icon=folium.Icon(color='blue')).add_to(map_obj)
            folium.Marker([lat2, lon2], popup=f"Ref 2 (dist: {dist2}km)", 
                         tooltip="Reference Point 2", icon=folium.Icon(color='green')).add_to(map_obj)
            folium.Marker([lat3, lon3], popup=f"Ref 3 (dist: {dist3}km)", 
                         tooltip="Reference Point 3", icon=folium.Icon(color='purple')).add_to(map_obj)
            
            # Add triangulated position
            folium.Marker([result_lat, result_lon], popup="Triangulated Position", 
                         tooltip="Result", icon=folium.Icon(color='red', prefix='fa', icon='location-dot')).add_to(map_obj)
            
            # Draw circles for distances
            folium.Circle([lat1, lon1], radius=dist1*1000, color='blue', fill=False, opacity=0.5).add_to(map_obj)
            folium.Circle([lat2, lon2], radius=dist2*1000, color='green', fill=False, opacity=0.5).add_to(map_obj)
            folium.Circle([lat3, lon3], radius=dist3*1000, color='purple', fill=False, opacity=0.5).add_to(map_obj)
            
            map_obj.save('templates/triangulation_map.html')
            
            return render_template('triangulation_result.html',
                                 result_lat=result_lat,
                                 result_lon=result_lon,
                                 lat1=lat1, lon1=lon1, dist1=dist1,
                                 lat2=lat2, lon2=lon2, dist2=dist2,
                                 lat3=lat3, lon3=lon3, dist3=dist3)
        except ValueError:
            return render_template('triangulation_form.html', error='Please enter valid numbers')
    
    return render_template('triangulation_form.html')

@app.route('/api/geocode', methods=['POST'])
def api_geocode():
    """API endpoint for geocoding locations"""
    data = request.get_json()
    location = data.get('location', '').strip()
    
    if not location:
        return jsonify({'error': 'Location required'}), 400
    
    coords = geocode_location(location)
    
    if coords:
        return jsonify({'lat': coords[0], 'lon': coords[1]})
    else:
        return jsonify({'error': 'Location not found'}), 404

if __name__ == "__main__":
    app.run(debug=True)
