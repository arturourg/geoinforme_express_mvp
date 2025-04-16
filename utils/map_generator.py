# utils/map_generator.py
import ee
import os
import requests # Necesitamos requests para descargar la imagen desde la URL
import shutil   # Para guardar el contenido descargado en un archivo

# Asegúrate de que el directorio de datos exista
DATA_DIR = 'data'
os.makedirs(DATA_DIR, exist_ok=True)

# Define los parámetros de visualización estándar (MANTENERlos como estaban)
ndvi_vis = {
    'min': -0.2, 'max': 0.9,
    'palette': ['FFFFFF', 'CE7E45', 'DF923D', 'F1B555', 'FCD163', '99B718',
                '74A901', '66A000', '529400', '3E8601', '207401', '056201',
                '004C00', '023B01', '012E01', '011D01', '011301']
}
ndwi_vis = {
    'min': -0.5, 'max': 0.5,
    'palette': ['#FF0000', '#FFA500', '#FFFF00', '#808080', '#00FFFF', '#0000FF']
}
nbr_vis = {
    'min': -0.5, 'max': 0.8,
     'palette': ['#0000FF', '#00FFFF', '#FFFF00', '#FFA500', '#FF0000', '#8B0000']
}
rgb_vis = {
    'bands': ['B4', 'B3', 'B2'],
    'min': 0,
    'max': 3000 # Ajustar según reflectancia Sentinel-2 L2A
}


def generate_map_image(image, vis_params, filename, aoi, title="Map"):
    """
    Genera una imagen de mapa (PNG) obteniendo una miniatura directamente de GEE
    usando getThumbURL y la guarda localmente.
    Devuelve la ruta a la imagen guardada.
    """
    filepath = os.path.join(DATA_DIR, filename)
    print(f"Intentando generar imagen de mapa vía getThumbURL: {filepath}")

    if not isinstance(image, ee.Image):
        print(f"ERROR: Objeto inválido pasado a generate_map_image. Se esperaba ee.Image, se obtuvo {type(image)}")
        return None
    if not isinstance(aoi, ee.geometry.Geometry):
         print(f"ERROR: AOI inválido pasado a generate_map_image. Se esperaba ee.Geometry, se obtuvo {type(aoi)}")
         return None

    try:
        # Define parámetros para la miniatura (thumbnail)
        # Puedes ajustar las dimensiones según necesites
        thumb_width = 512
        thumb_height = 512

        # Obtén los límites del AOI para definir la región de la miniatura
        # getInfo() es necesario aquí para obtener las coordenadas en el lado del cliente
        region = aoi.bounds(maxError=1).getInfo()['coordinates'] # Usamos bounds() para obtener un rectángulo

        # Prepara la imagen para visualización aplicando los parámetros directamente
        # Es importante asegurarse de que vis_params contenga claves válidas para visualize()
        img_to_visualize = None
        if 'bands' in vis_params: # Caso RGB
            img_to_visualize = image.visualize(
                bands=vis_params.get('bands'),
                min=vis_params.get('min', 0),
                max=vis_params.get('max', 3000)
                # Otros params como gamma, opacity podrían ir aquí
            )
        else: # Caso índices de una banda con paleta
             img_to_visualize = image.visualize(
                min=vis_params.get('min', 0),
                max=vis_params.get('max', 1),
                palette=vis_params.get('palette')
             )

        if img_to_visualize is None:
             raise ValueError("No se pudo crear la imagen visualizada desde los parámetros.")

        # Obtén la URL de la miniatura desde Earth Engine
        # Pasamos la imagen visualizada, la región, dimensiones y formato
        thumb_url = img_to_visualize.getThumbURL({
            'region': region,
            'dimensions': f'{thumb_width}x{thumb_height}', # Formato "WIDTHxHEIGHT"
            'format': 'png'
        })
        print(f"DEBUG: URL de Miniatura GEE generada: {thumb_url}")

        # Descarga la imagen desde la URL usando la librería requests
        response = requests.get(thumb_url, stream=True)
        response.raise_for_status() # Lanza excepción si hay error HTTP (ej. 404, 500)

        # Guarda la imagen descargada en el archivo destino
        with open(filepath, 'wb') as out_file:
            shutil.copyfileobj(response.raw, out_file)

        # Libera la conexión
        del response

        # Verifica si el archivo se creó y no está vacío
        if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
            print(f"Imagen de mapa generada exitosamente vía getThumbURL: {filepath}")
            return filepath
        else:
            print(f"ERROR: Archivo de imagen no encontrado o vacío después de descargar: {filepath}")
            return None

    except ee.EEException as e:
         # Errores específicos de Google Earth Engine
         print(f"ERROR durante operación GEE en generate_map_image (getThumbURL): {e}")
         return None
    except requests.exceptions.RequestException as e:
         # Errores al descargar la URL (red, etc.)
         print(f"ERROR descargando miniatura desde URL de GEE: {e}")
         return None
    except Exception as e:
        # Cualquier otro error inesperado
        print(f"ERROR generando imagen de mapa {filename} vía getThumbURL: {e}")
        import traceback
        traceback.print_exc() # Imprime el traceback detallado para depuración
        return None