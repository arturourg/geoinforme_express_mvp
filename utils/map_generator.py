# utils/map_generator.py
import ee
import geemap
import os
import matplotlib.pyplot as plt # Matplotlib is used by geemap for static plots

# Ensure data directory exists
DATA_DIR = 'data'
os.makedirs(DATA_DIR, exist_ok=True)

# Define standard visualization parameters
ndvi_vis = {
    'min': -0.2, 'max': 0.9,
    'palette': ['FFFFFF', 'CE7E45', 'DF923D', 'F1B555', 'FCD163', '99B718',
                '74A901', '66A000', '529400', '3E8601', '207401', '056201',
                '004C00', '023B01', '012E01', '011D01', '011301']
}

ndwi_vis = {
    'min': -0.5, 'max': 0.5,
    'palette': ['#FF0000', '#FFA500', '#FFFF00', '#808080', '#00FFFF', '#0000FF'] # Red/Orange (Dry) to Blue (Wet)
}

nbr_vis = {
    'min': -0.5, 'max': 0.8, # Typical NBR range for visualization
     'palette': ['#0000FF', '#00FFFF', '#FFFF00', '#FFA500', '#FF0000', '#8B0000'] # Blue (low severity) to Dark Red (high severity)
}

rgb_vis = {
    'bands': ['B4', 'B3', 'B2'], # True color (Red, Green, Blue)
    'min': 0,
    'max': 3000 # Adjust max based on typical reflectance values for Sentinel-2 L2A
}

def generate_map_image(image, vis_params, filename, aoi, title="Map"):
    """
    Generates a static map image using geemap and saves it.
    Returns the path to the saved image.
    """
    filepath = os.path.join(DATA_DIR, filename)
    print(f"Attempting to generate map image: {filepath}")

    try:
        # Create a map centered on the AOI
        map_viz = geemap.Map(center=aoi.centroid().getInfo()['coordinates'][::-1], zoom=11) # Reverse coords for lat,lon

        # Add the layer to the map
        map_viz.addLayer(image.clip(aoi), vis_params, title)
        map_viz.add_colorbar(vis_params, label=title) # Add colorbar using the vis params

        # Add AOI boundary to the map for context
        style = {'color': 'black', 'fillColor': '00000000'} # Transparent fill
        map_viz.addLayer(aoi.style(**style), {}, 'Area of Interest')

        # Ensure the map is sized appropriately before saving
        # This part is tricky with geemap's static image export. Let's try default first.
        # If maps are too small/cropped, might need different approach or library.

        print(f"Saving map to {filepath}...")
        map_viz.to_image(filename=filepath, monitor=1) # Monitor adds scale bar

        # Check if file exists after saving
        if os.path.exists(filepath):
            print(f"Successfully generated map image: {filepath}")
            return filepath
        else:
            print(f"ERROR: Map image file not found after saving attempt: {filepath}")
            # Attempt fallback using matplotlib if geemap fails (more complex setup)
            # For MVP, just return None if geemap fails
            return None

    except ee.EEException as e:
         print(f"ERROR during GEE operation in map generation: {e}")
         return None
    except Exception as e:
        print(f"ERROR generating map image {filename}: {e}")
        import traceback
        traceback.print_exc() # Print detailed traceback for debugging
        return None

# Consider adding functions for Folium or Plotly if static images prove difficult
# def generate_folium_map(image, vis_params, aoi, title): ... return folium_map_object