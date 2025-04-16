# utils/index_calculator.py
import ee

# Initialize Earth Engine - Assumes authentication is done via CLI
try:
    ee.Initialize()
    ee.Initialize(project='geoinforme')  # Reemplaza con tu ID real ()from utils import index_calculator
    print("Google Earth Engine Initialized Successfully.")
except ee.EEException as e:
    print(f"ERROR: Failed to initialize Earth Engine: {e}")
    print("Please ensure you have authenticated via the command line ('earthengine authenticate').")
    # In a real app, you might exit or raise a custom exception
    # For MVP, we print the error and continue, GEE calls will fail later.
except Exception as e:
    print(f"An unexpected error occurred during EE initialization: {e}")


def calculate_ndvi(image):
    """Calculates NDVI (Normalized Difference Vegetation Index)."""
    try:
        return image.normalizedDifference(['B8', 'B4']).rename('NDVI') # Sentinel-2 bands: B8=NIR, B4=Red
    except Exception as e:
        print(f"Error calculating NDVI: {e}. Ensure image has B8 and B4 bands.")
        # Return a dummy band or raise an error
        return None # Or ee.Image(0).rename('NDVI') if you need an Image object

def calculate_ndwi(image):
    """Calculates NDWI (Normalized Difference Water Index - McFeeters)."""
    try:
        # Using Green (B3) and NIR (B8) for Sentinel-2
        return image.normalizedDifference(['B3', 'B8']).rename('NDWI')
    except Exception as e:
        print(f"Error calculating NDWI: {e}. Ensure image has B3 and B8 bands.")
        return None

def calculate_nbr(image):
    """Calculates NBR (Normalized Burn Ratio)."""
    try:
        # Using NIR (B8) and SWIR (B12) for Sentinel-2
        return image.normalizedDifference(['B8', 'B12']).rename('NBR')
    except Exception as e:
        print(f"Error calculating NBR: {e}. Ensure image has B8 and B12 bands.")
        return None

# Add other indices here as needed (MSI, BAI, SAVI etc. for future iterations)