from flask import Flask, render_template, request
import math
import folium

app = Flask(__name__)

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
    return distance

# Triangulation function
def triangulate_position(p1, p2, p3, d1, d2, d3):
    # Simplified triangulation (to be expanded with full logic)
    lat = (p1[0] * d1 + p2[0] * d2 + p3[0] * d3) / (d1 + d2 + d3)
    lon = (p1[1] * d1 + p2[1] * d2 + p3[1] * d3) / (d1 + d2 + d3)
    
    return lat, lon

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        search_query = request.form.get('location')
        lat, lon = 51.5074, -0.1278  # Example: London coordinates
        map = folium.Map(location=[lat, lon], zoom_start=12)
        folium.Marker([lat, lon], popup="Location found").add_to(map)
        map.save('templates/map.html')
        return render_template('map.html')
    
    return render_template('index.html')

@app.route('/distance', methods=['GET', 'POST'])
def calculate_distance():
    if request.method == 'POST':
        lat1 = float(request.form['lat1'])
        lon1 = float(request.form['lon1'])
        lat2 = float(request.form['lat2'])
        lon2 = float(request.form['lon2'])
        
        distance = haversine((lat1, lon1), (lat2, lon2))
        return render_template('distance_result.html', distance=distance)
    
    return render_template('distance_form.html')

@app.route('/triangulate', methods=['GET', 'POST'])
def triangulate():
    if request.method == 'POST':
        lat1 = float(request.form['lat1'])
        lon1 = float(request.form['lon1'])
        dist1 = float(request.form['dist1'])
        
        lat2 = float(request.form['lat2'])
        lon2 = float(request.form['lon2'])
        dist2 = float(request.form['dist2'])
        
        lat3 = float(request.form['lat3'])
        lon3 = float(request.form['lon3'])
        dist3 = float(request.form['dist3'])
        
        result_lat, result_lon = triangulate_position(
            (lat1, lon1), (lat2, lon2), (lat3, lon3),
            dist1, dist2, dist3
        )
        return f"Triangulated position: Latitude {result_lat}, Longitude {result_lon}"
    
    return render_template('triangulation_form.html')

if __name__ == "__main__":
    app.run(debug=True)
