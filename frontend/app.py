# frontend/app.py
import streamlit as st
import ee
ee.Initialize(project='geoinforme')  # Reemplaza con tu ID real ()from utils import index_calculator
print(ee.data.getAssetRoots())  # Debe mostrar tus proyectos y assets accesibles.
import os
import time
from backend import gee_processor
from reports import pdf_generator
from utils import helpers

# --- Page Configuration ---
st.set_page_config(
    page_title="GeoInforme Express MVP",
    page_icon="🛰️",
    layout="centered"
)
# --- Initialize Session State ---
if 'aoi_params' not in st.session_state:
    st.session_state.aoi_params = None # Guardará {'lat':..., 'lon':..., 'radius_km':...} o {'geojson_string': "..."}
if 'aoi_type' not in st.session_state:
    st.session_state.aoi_type = None # Será 'coords' o 'geojson'
if 'pdf_report_path' not in st.session_state:
    st.session_state.pdf_report_path = None
if 'gee_initialized' not in st.session_state:
    st.session_state.gee_initialized = False # Nueva bandera para verificar la inicialización de GEE
    
# --- GEE Initialization Check ---
# Although initialized elsewhere, good to have a check/reminder here
if not st.session_state.gee_initialized:
    st.sidebar.info("Intentando conectar a Google Earth Engine...")
    try:
        # Intenta una operación simple para verificar la conexión
        _ = ee.Geometry.Point([0, 0]).getInfo()
        st.session_state.gee_initialized = True # Marcar como inicializado para esta sesión
        st.sidebar.success("Google Earth Engine Conectado")
        # Recargar la página una vez conectado puede ayudar a limpiar el estado inicial
        # st.experimental_rerun() # Descomentar con precaución si es necesario
    except Exception as e:
         st.sidebar.error(f"Error conectando a GEE: {e}. Revisa la autenticación ('earthengine authenticate').")
         st.warning("La aplicación podría no funcionar correctamente sin conexión a GEE.")
         st.session_state.gee_initialized = False # Asegurarse de que sigue falso si falla
else:
    # Si ya está inicializado, solo muestra el éxito (opcional)
    st.sidebar.success("Google Earth Engine Conectado")

# --- Application Title ---
st.title("🛰️ GeoInforme Express MVP")
st.markdown("Generador rápido de informes satelitales básicos.")

# --- Input Form ---
st.header("1. Define tu Área de Interés (AOI)")

# Option Tabs for AOI definition
tab1, tab2 = st.tabs(["Coordenadas + Radio", "Subir Archivo GeoJSON/KML"])

aoi = None # Initialize AOI variable

with tab1:
    st.subheader("Opción A: Coordenadas Centrales y Radio")
    col1, col2 = st.columns(2)
    with col1:
        lat = st.number_input("Latitud Central", min_value=-90.0, max_value=90.0, value=-36.82, format="%.6f") # Example: Concepción, Chile
    with col2:
        lon = st.number_input("Longitud Central", min_value=-180.0, max_value=180.0, value=-73.05, format="%.6f") # Example: Concepción, Chile
    radius_km = st.number_input("Radio (km)", min_value=0.1, max_value=50.0, value=5.0, step=0.5)
    if st.button("Usar Coordenadas", key="coord_btn"):
        # Guarda los parámetros, no la geometría
        st.session_state.aoi_params = {'lat': lat, 'lon': lon, 'radius_km': radius_km}
        st.session_state.aoi_type = 'coords'
        if st.session_state.aoi_params:
            st.success("Parámetros AOI (coords) guardados en sesión.")
            # Limpia el otro tipo por si acaso
            # st.session_state.aoi = None # Ya no usamos st.session_state.aoi
        else:
            # Esto no debería pasar si lat/lon/radius tienen valores
            st.error("Error al guardar parámetros AOI.")
            st.session_state.aoi_params = None
            st.session_state.aoi_type = None


with tab2:
    st.subheader("Opción B: Subir Archivo Geoespacial")
    uploaded_file = st.file_uploader("Carga tu archivo .geojson o .kml", type=['geojson', 'kml'])
    if uploaded_file is not None:
        file_type = uploaded_file.name.split('.')[-1].lower()
        if file_type == 'geojson':
            try:
                # Lee el contenido del archivo UNA VEZ
                geojson_content = uploaded_file.read().decode("utf-8")
                # Intenta cargarlo para validación rápida (opcional pero bueno)
                _ = geojson.loads(geojson_content)
                # Guarda el string
                st.session_state.aoi_params = {'geojson_string': geojson_content}
                st.session_state.aoi_type = 'geojson'
                st.success("Contenido GeoJSON guardado en sesión.")
                # Limpia el otro tipo por si acaso
                # st.session_state.aoi = None # Ya no usamos st.session_state.aoi
            except Exception as e:
                st.error(f"Error al leer/validar o guardar GeoJSON: {e}")
                st.session_state.aoi_params = None
                st.session_state.aoi_type = None
        elif file_type == 'kml':
            # aoi = helpers.parse_kml(uploaded_file) # KML Parsing TBD
            st.warning("La carga de KML aún no está completamente implementada en el MVP. Intenta con GeoJSON.")
            # if aoi:
            #     st.success("Archivo KML procesado (básico).")
            # else:
            #     st.error("Error al procesar el archivo KML.")
        else:
            st.error("Tipo de archivo no soportado.")

# --- Date Range Selection ---
st.header("2. Selecciona el Período de Tiempo")
# Simple options for MVP - more complex date pickers later
time_period = st.selectbox(
    "Analizar imágenes de:",
    ("Último mes", "Últimos 3 meses", "Últimos 6 meses"), # Add more options if needed
    index=0 # Default to 'Último mes'
)
start_date, end_date = helpers.get_date_range(time_period)
st.caption(f"Se buscarán imágenes entre {start_date} y {end_date} con <20% de nubes.")

# --- Report Generation Trigger ---
st.header("3. Generar Informe")

# Placeholders for results
pdf_path = None
report_data = None

if st.session_state.aoi_params is None: # NEW - Verifica si hay parámetros guardados
    st.warning("Por favor, define un Área de Interés (AOI) usando una de las opciones anteriores.")
    # print("DEBUG: Botón no activo porque AOI Params es None.") # Actualiza debug msg
else:
    print(f"DEBUG: Parámetros AOI definidos ({st.session_state.aoi_type}). Botón activo.") # Actualiza debug msg
    # print("DEBUG: Justo antes de evaluar st.button") # Puedes quitar/mantener

    # --- Botón Principal ---
    if st.button("🚀 Generar Informe Ahora"):
        print("DEBUG: Botón 'Generar Informe Ahora' PRESIONADO.")
        if not st.session_state.gee_initialized:
            st.error("Error: Google Earth Engine no está inicializado correctamente. No se puede continuar.")
        else:
            # --- RECREAR ee.Geometry AHORA ---
            current_aoi = None # Variable local para la geometría
            recreation_error = None
            try:
                if st.session_state.aoi_type == 'coords':
                    params = st.session_state.aoi_params
                    current_aoi = helpers.get_ee_geometry_from_coords(params['lat'], params['lon'], params['radius_km'])
                    print("DEBUG: Recreado AOI desde Coords guardados")
                elif st.session_state.aoi_type == 'geojson':
                    params = st.session_state.aoi_params
                    geojson_string = params.get('geojson_string')
                    if geojson_string:
                        gj = geojson.loads(geojson_string)
                        # Extraer geometría (mismo código que en helpers.parse_geojson)
                        geometry_data = None
                        if gj['type'] == 'FeatureCollection':
                            if gj['features']:
                                geometry_data = gj['features'][0]['geometry']
                        elif gj['type'] == 'Feature':
                            geometry_data = gj['geometry']
                        elif gj['type'] in ['Polygon', 'MultiPolygon', 'Point', 'LineString', 'MultiPoint', 'MultiLineString']:
                            geometry_data = gj

                        if geometry_data:
                            current_aoi = ee.Geometry(geometry_data)
                            print("DEBUG: Recreado AOI desde GeoJSON String guardado")
                        else:
                            recreation_error = "No se encontró geometría válida en el GeoJSON guardado."
                    else:
                        recreation_error = "No se encontró el string GeoJSON en el estado."
                else:
                    recreation_error = "Tipo de AOI desconocido en el estado."

                # Verificar si la recreación fue exitosa
                if current_aoi is None:
                    st.error(f"Error crítico: No se pudo recrear la geometría AOI. {recreation_error or ''}")
                else:
                    print(f"DEBUG: AOI Recreado Exitosamente (tipo: {type(current_aoi)})")
                    # --- PROCEDER CON EL PROCESAMIENTO ---
                    with st.spinner(f"Procesando AOI y generando informe para el período {start_date} a {end_date}... Esto puede tardar unos minutos."):
                        print("DEBUG: Entrando al bloque spinner...")
                        try:
                            print("DEBUG: Ejecutando limpieza de archivos...")
                            helpers.cleanup_temp_files()

                            print(f"DEBUG: Llamando a process_aoi con AOI recreado y fechas {start_date}-{end_date}...")
                            # Usa la geometría recién creada
                            processing_results = gee_processor.process_aoi(current_aoi, start_date, end_date)
                            print(f"DEBUG: Resultado de process_aoi: {processing_results}")

                            # ... (resto del código de procesamiento y generación de PDF como estaba antes) ...
                            # ... (asegúrate de actualizar st.session_state.pdf_report_path si la generación es exitosa) ...
                            if processing_results and 'error' not in processing_results:
                                st.info("✅ Procesamiento GEE completado. Generando PDF...")
                                pdf_report_path = pdf_generator.generate_pdf_report(processing_results)
                                if pdf_report_path and os.path.exists(pdf_report_path):
                                    st.success("🎉 ¡Informe PDF generado con éxito!")
                                    st.session_state.pdf_report_path = pdf_report_path # Guarda para descarga
                                else:
                                    st.error("❌ Error al generar el archivo PDF del informe.")
                                    st.session_state.pdf_report_path = None
                            elif processing_results and 'error' in processing_results:
                                st.error(f"❌ Error durante el procesamiento: {processing_results['error']}")
                                st.session_state.pdf_report_path = None
                            else:
                                st.error("❌ Error desconocido durante el procesamiento GEE.")
                                st.session_state.pdf_report_path = None

                        except ee.EEException as e:
                            # ... (manejo de excepciones como estaba) ...
                            st.session_state.pdf_report_path = None
                        except Exception as e:
                            # ... (manejo de excepciones como estaba) ...
                            st.session_state.pdf_report_path = None
                    print("DEBUG: Saliendo del bloque spinner.")

            except Exception as geo_rec_error:
                st.error(f"Error inesperado durante la recreación de la geometría AOI: {geo_rec_error}")
                print(f"DEBUG: EXCEPCIÓN en recreación AOI: {geo_rec_error}")

# --- Download Button ---
# This part should appear *after* the button is pressed and report_data is populated
# We use session state to keep track of the generated PDF path across reruns
if 'pdf_report_path' not in st.session_state:
    st.session_state.pdf_report_path = None

if report_data: # If generation was successful in the latest run
    st.session_state.pdf_report_path = report_data

if st.session_state.pdf_report_path and os.path.exists(st.session_state.pdf_report_path):
    st.markdown("---")
    st.subheader("Descargar Informe")
    with open(st.session_state.pdf_report_path, "rb") as pdf_file:
        pdf_bytes = pdf_file.read()

    st.download_button(
        label="⬇️ Descargar PDF",
        data=pdf_bytes,
        file_name=os.path.basename(st.session_state.pdf_report_path),
        mime="application/pdf",
        on_click=lambda: setattr(st.session_state, 'pdf_report_path', None) # Clear path after download attempt
    )
    st.caption("El archivo se eliminará del servidor después de la descarga o al generar un nuevo informe.")
else:
    # Optional: Clear the state if the file doesn't exist anymore
     if st.session_state.pdf_report_path:
          st.session_state.pdf_report_path = None


# --- Optional: Display logs or more detailed feedback ---
# st.expander("Ver Logs (Avanzado)")...