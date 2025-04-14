# backend/gee_processor.py
import ee
from utils import index_calculator
from utils.map_generator import generate_map_image, ndvi_vis, nbr_vis, ndwi_vis, rgb_vis
import time
import os

# Define data directory
DATA_DIR = 'data'

# Initialize Earth Engine (redundant if already done in index_calculator, but safe)
try:
    if not ee.data._credentials:
        ee.Initialize()
except Exception as e:
    print(f"WARNING: Could not initialize EE in gee_processor: {e}")
    # The app might fail if EE wasn't initialized elsewhere

def get_sentinel2_image(aoi, start_date, end_date, cloud_cover_max=20):
    """
    Gets the least cloudy Sentinel-2 L2A image for the AOI and date range.
    """
    try:
        print(f"Fetching Sentinel-2 image for AOI between {start_date} and {end_date}...")
        s2_collection = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED') \
            .filterBounds(aoi) \
            .filterDate(start_date, end_date) \
            .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', cloud_cover_max))

        # Check if any images are found
        count = s2_collection.size().getInfo()
        print(f"Found {count} images matching criteria.")

        if count == 0:
            print("WARNING: No suitable Sentinel-2 images found for the specified criteria.")
            return None # Indicate no image found

        # Select the least cloudy image
        image = s2_collection.sort('CLOUDY_PIXEL_PERCENTAGE').first()

        # Ensure the image is not null (can happen even if count > 0 in rare cases)
        if image is None:
             print("WARNING: Sorted collection resulted in a null image.")
             return None

        print(f"Selected image ID: {image.id().getInfo()} with {image.get('CLOUDY_PIXEL_PERCENTAGE').getInfo()}% cloud cover.")
        return image # Return the ee.Image object

    except ee.EEException as e:
        print(f"ERROR during GEE operation in get_sentinel2_image: {e}")
        return None
    except Exception as e:
        print(f"ERROR in get_sentinel2_image: {e}")
        return None


def process_aoi(aoi, start_date, end_date):
    """
    Main processing function: gets image, calculates indices, generates maps.
    Returns a dictionary with results (image paths, metadata) or None on failure.
    """
    if not isinstance(aoi, ee.geometry.Geometry):
        print("ERROR: Invalid AOI provided to process_aoi. Expected ee.Geometry.")
        return None

    print("Starting AOI processing...")
    start_time = time.time()

    # 1. Get Sentinel-2 Image
    base_image = get_sentinel2_image(aoi, start_date, end_date)
    if base_image is None:
        print("Processing failed: Could not retrieve a suitable base image.")
        return {'error': "No suitable satellite image found for the period and AOI. Try adjusting dates or AOI."}

    # Add timeout or retry logic here in a production system

    # 2. Calculate Indices
    print("Calculating indices...")
    ndvi = index_calculator.calculate_ndvi(base_image)
    ndwi = index_calculator.calculate_ndwi(base_image)
    nbr = index_calculator.calculate_nbr(base_image)

    # Check if index calculation failed
    if ndvi is None or ndwi is None or nbr is None:
        print("Processing failed: Error during index calculation.")
        return {'error': "Failed to calculate one or more indices. Image might lack required bands."}

    # 3. Generate Map Images
    print("Generating map images...")
    timestamp = time.strftime("%Y%m%d-%H%M%S") # Unique identifier for this run
    results = {'metadata': {
        'aoi_bounds': aoi.bounds().getInfo()['coordinates'],
        'image_id': base_image.id().getInfo(),
        'image_date': ee.Date(base_image.get('system:time_start')).format('YYYY-MM-dd').getInfo(),
        'cloud_cover': base_image.get('CLOUDY_PIXEL_PERCENTAGE').getInfo(),
        'processing_timestamp': timestamp
    }}

    map_tasks = {
        'rgb': (base_image, rgb_vis, f'rgb_{timestamp}.png', 'True Color (RGB)'),
        'ndvi': (ndvi, ndvi_vis, f'ndvi_{timestamp}.png', 'NDVI'),
        'ndwi': (ndwi, ndwi_vis, f'ndwi_{timestamp}.png', 'NDWI'),
        'nbr': (nbr, nbr_vis, f'nbr_{timestamp}.png', 'NBR')
    }

    image_paths = {}
    for key, (img, vis, filename, title) in map_tasks.items():
        filepath = generate_map_image(img, vis, filename, aoi, title)
        if filepath:
            image_paths[key] = filepath
        else:
            print(f"WARNING: Failed to generate map for {key}")
            # Decide if failure to generate one map should halt everything
            # For MVP, we can continue and report missing maps

    results['image_paths'] = image_paths

    # Check if any maps were generated
    if not image_paths:
        print("Processing failed: Could not generate any map images.")
        return {'error': "Failed to generate map visualizations."}


    end_time = time.time()
    print(f"AOI processing finished in {end_time - start_time:.2f} seconds.")
    return results