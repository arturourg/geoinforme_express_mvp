# utils/helpers.py
import ee
import geojson
import tempfile
import os
import shutil
from datetime import datetime, timedelta

def parse_geojson(uploaded_file):
    """Parses an uploaded GeoJSON file and returns an ee.Geometry."""
    try:
        # Streamlit file uploader gives a file-like object
        content = uploaded_file.read().decode("utf-8")
        gj = geojson.loads(content)

        # Extract geometry - handle FeatureCollection, Feature, or Geometry directly
        if gj['type'] == 'FeatureCollection':
            if not gj['features']:
                 raise ValueError("GeoJSON FeatureCollection is empty.")
            # Use the geometry of the first feature for simplicity in MVP
            geometry = gj['features'][0]['geometry']
        elif gj['type'] == 'Feature':
            geometry = gj['geometry']
        elif gj['type'] in ['Polygon', 'MultiPolygon', 'Point', 'LineString', 'MultiPoint', 'MultiLineString']:
             geometry = gj
        else:
            raise ValueError(f"Unsupported GeoJSON type: {gj['type']}")

        # Convert GeoJSON geometry to ee.Geometry
        # GEE expects coordinates in [longitude, latitude] order
        ee_geometry = ee.Geometry(geometry)
        print("Successfully parsed GeoJSON to ee.Geometry.")
        return ee_geometry
    except Exception as e:
        print(f"Error parsing GeoJSON file: {e}")
        return None

def parse_kml(uploaded_file):
    """Parses an uploaded KML file (basic implementation)."""
    # KML parsing is more complex, often needing libraries like fastkml or pykml
    # For MVP, we might just show a message that it's not fully supported yet
    # Or attempt a very basic extraction if structure is known and simple (e.g., first Polygon)
    print("KML parsing is complex. For MVP, try converting KML to GeoJSON first.")
    # Placeholder: Read content, maybe use a basic XML parser if desperate
    # content = uploaded_file.read().decode("utf-8")
    # For now, return None
    return None

def get_ee_geometry_from_coords(lat, lon, radius_km):
    """Creates a circular ee.Geometry from center coords and radius."""
    try:
        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            raise ValueError("Invalid latitude or longitude values.")
        if radius_km <= 0:
             raise ValueError("Radius must be positive.")
        point = ee.Geometry.Point([lon, lat])
        # Buffer takes radius in meters
        buffered_aoi = point.buffer(radius_km * 1000)
        print(f"Created circular AOI: Lat={lat}, Lon={lon}, Radius={radius_km}km")
        return buffered_aoi
    except Exception as e:
        print(f"Error creating geometry from coordinates: {e}")
        return None

def get_date_range(time_period_option):
    """Gets start and end dates based on a selected option."""
    # Simple implementation for MVP
    end_date = datetime.now()
    if time_period_option == "Último mes":
        start_date = end_date - timedelta(days=30)
    elif time_period_option == "Últimos 3 meses":
        start_date = end_date - timedelta(days=90)
    elif time_period_option == "Últimos 6 meses":
         start_date = end_date - timedelta(days=180)
    else: # Default to last month
        start_date = end_date - timedelta(days=30)

    # Format as YYYY-MM-DD strings
    return start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')

def cleanup_temp_files(directory='data'):
    """Removes files from the temporary data directory."""
    print(f"Cleaning up temporary files in {directory}...")
    for filename in os.listdir(directory):
        # Avoid removing .gitkeep or other essential files if any
        if filename == '.gitkeep':
            continue
        file_path = os.path.join(directory, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
            print(f"Removed: {file_path}")
        except Exception as e:
            print(f'Failed to delete {file_path}. Reason: {e}')