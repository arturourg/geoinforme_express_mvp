# frontend/app.py
import streamlit as st
import ee
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

# --- GEE Initialization Check ---
# Although initialized elsewhere, good to have a check/reminder here
try:
    # A simple check like listing root folders
    ee.data.listAssets({'parent': 'users/username'}) # Replace with a valid path or use a different check
    st.sidebar.success("Google Earth Engine Conectado")
except Exception as e:
     st.sidebar.error(f"Error conectando a GEE: {e}. Asegúrate de haber corrido 'earthengine authenticate' en tu terminal.")
     st.warning("La aplicación no funcionará sin conexión a GEE.")
     # Optionally disable the form if GEE fails
     # st.stop()

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
        aoi = helpers.get_ee_geometry_from_coords(lat, lon, radius_km)
        if aoi:
            st.success("AOI circular creada.")
            # Optionally display map preview here using geemap.st_map (might slow down MVP)
        else:
            st.error("Error al crear AOI desde coordenadas.")


with tab2:
    st.subheader("Opción B: Subir Archivo Geoespacial")
    uploaded_file = st.file_uploader("Carga tu archivo .geojson o .kml", type=['geojson', 'kml'])
    if uploaded_file is not None:
        file_type = uploaded_file.name.split('.')[-1].lower()
        if file_type == 'geojson':
            aoi = helpers.parse_geojson(uploaded_file)
            if aoi:
                st.success("Archivo GeoJSON procesado. Usando la geometría encontrada.")
            else:
                st.error("Error al procesar el archivo GeoJSON.")
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

if aoi is None:
    st.warning("Por favor, define un Área de Interés (AOI) usando una de las opciones anteriores.")
else:
    if st.button("🚀 Generar Informe Ahora"):
        with st.spinner(f"Procesando AOI y generando informe para el período {start_date} a {end_date}... Esto puede tardar unos minutos."):
            try:
                # Clean up old files before generating new ones
                helpers.cleanup_temp_files()

                # Process AOI
                processing_results = gee_processor.process_aoi(aoi, start_date, end_date)

                if processing_results and 'error' not in processing_results:
                    st.info("✅ Procesamiento GEE completado. Generando PDF...")
                    # Generate PDF
                    pdf_report_path = pdf_generator.generate_pdf_report(processing_results)

                    if pdf_report_path and os.path.exists(pdf_report_path):
                        st.success("🎉 ¡Informe PDF generado con éxito!")
                        report_data = pdf_report_path # Store path for download button
                    else:
                        st.error("❌ Error al generar el archivo PDF del informe.")
                        st.json(processing_results) # Show GEE results if PDF failed

                elif processing_results and 'error' in processing_results:
                     st.error(f"❌ Error durante el procesamiento: {processing_results['error']}")
                else:
                    st.error("❌ Error desconocido durante el procesamiento GEE.")

            except ee.EEException as e:
                 st.error(f"❌ Error de Google Earth Engine: {e}")
                 st.info("Verifica tu conexión y autenticación con GEE ('earthengine authenticate').")
            except Exception as e:
                st.error(f"❌ Ocurrió un error inesperado: {e}")
                import traceback
                st.text(traceback.format_exc()) # Show traceback for debugging

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