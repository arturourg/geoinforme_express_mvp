# GeoInforme Express - MVP

Este proyecto es un Producto Mínimo Viable (MVP) para GeoInforme Express, una herramienta para generar informes satelitales básicos de forma rápida y accesible.

**Objetivo del MVP:** Validar la viabilidad técnica de generar automáticamente informes PDF con mapas de índices (NDVI, NDWI, NBR) para un Área de Interés (AOI) definida por el usuario, utilizando Google Earth Engine y Python.

## Funcionalidades del MVP

* Interfaz web simple (Streamlit) para definir el AOI mediante:
    * Coordenadas centrales y radio.
    * Subida de archivo GeoJSON.
* Selección de un período de tiempo relativo (último mes, 3 meses, 6 meses).
* Procesamiento automático usando Google Earth Engine (GEE) para obtener imágenes Sentinel-2.
* Cálculo de índices: NDVI, NDWI, NBR.
* Generación de mapas visuales para cada índice y una imagen RGB.
* Creación de un informe en formato PDF que incluye los mapas y metadatos básicos.
* Botón para descargar el informe PDF generado.

## Requerimientos Técnicos

* Python >= 3.9
* Google Earth Engine Python API configurada y autenticada.
* Librerías listadas en `requirements.txt`.

## Instrucciones de Uso

1.  **Clonar el Repositorio:**
    ```bash
    git clone <URL_DEL_REPOSITORIO>
    cd geoinforme_express_mvp
    ```

2.  **Crear un Entorno Virtual (Recomendado):**
    ```bash
    python -m venv venv
    # Windows
    venv\Scripts\activate
    # macOS/Linux
    source venv/bin/activate
    ```

3.  **Instalar Dependencias:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Autenticar Google Earth Engine:**
    * Necesitas una cuenta de Google habilitada para usar Google Earth Engine. Regístrate en [https://earthengine.google.com/](https://earthengine.google.com/).
    * Una vez tengas acceso, corre el siguiente comando en tu terminal y sigue las instrucciones para iniciar sesión y autenticarte:
        ```bash
        earthengine authenticate
        ```
    * **IMPORTANTE:** La aplicación no funcionará si no completas este paso.

5.  **Lanzar la Aplicación Streamlit:**
    ```bash
    streamlit run frontend/app.py
    ```
    Esto abrirá la aplicación en tu navegador web.

6.  **Generar un Informe de Prueba:**
    * Abre la aplicación en tu navegador.
    * Define un AOI usando coordenadas (los valores por defecto apuntan a Concepción, Chile) o subiendo un archivo GeoJSON válido.
    * Selecciona un período de tiempo.
    * Haz clic en el botón "🚀 Generar Informe Ahora".
    * Espera mientras se procesan los datos (puede tardar unos minutos). Verás un indicador de carga.
    * Si todo va bien, aparecerá un mensaje de éxito y un botón para descargar el informe PDF.
    * Si ocurren errores, la aplicación mostrará mensajes indicando el problema. Revisa la consola donde lanzaste `streamlit run` para ver logs más detallados.

## Estructura del Proyecto