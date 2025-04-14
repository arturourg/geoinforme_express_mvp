# reports/pdf_generator.py
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.units import inch, cm
import os
import time

# Ensure data directory exists (where PDF will be saved)
DATA_DIR = 'data'
os.makedirs(DATA_DIR, exist_ok=True)

def generate_pdf_report(results, filename_prefix="GeoInformeExpress"):
    """
    Generates a PDF report from the processing results.
    Saves the PDF to the data/ directory.
    Returns the path to the generated PDF.
    """
    timestamp = results.get('metadata', {}).get('processing_timestamp', time.strftime("%Y%m%d-%H%M%S"))
    pdf_filename = f"{filename_prefix}_{timestamp}.pdf"
    pdf_filepath = os.path.join(DATA_DIR, pdf_filename)
    print(f"Generating PDF report: {pdf_filepath}")

    try:
        doc = SimpleDocTemplate(pdf_filepath)
        styles = getSampleStyleSheet()
        story = []

        # --- Title Page ---
        title_style = styles['h1']
        title_style.alignment = TA_CENTER
        story.append(Paragraph("GeoInforme Express - Reporte Satelital", title_style))
        story.append(Spacer(1, 0.5*inch))

        # --- Metadata Section ---
        meta = results.get('metadata', {})
        meta_style = styles['Normal']
        meta_style.alignment = TA_LEFT
        story.append(Paragraph(f"<b>Fecha de Procesamiento:</b> {timestamp}", meta_style))
        story.append(Paragraph(f"<b>Imagen Base:</b> {meta.get('image_id', 'N/A')}", meta_style))
        story.append(Paragraph(f"<b>Fecha Imagen:</b> {meta.get('image_date', 'N/A')}", meta_style))
        story.append(Paragraph(f"<b>Cobertura Nubosa Estimada:</b> {meta.get('cloud_cover', 'N/A'):.2f}%", meta_style))
        # Add AOI info - maybe a small map or coordinates? For MVP, just text.
        # story.append(Paragraph(f"<b>Área de Interés (Bounds):</b> {meta.get('aoi_bounds', 'N/A')}", meta_style))
        story.append(Spacer(1, 0.3*inch))

        # --- Map Sections ---
        image_paths = results.get('image_paths', {})
        available_maps = {
            'rgb': ('Imagen Color Verdadero (RGB)', 'Referencia visual del área.'),
            'ndvi': ('Índice de Vegetación (NDVI)', 'Valores altos (verde) indican vegetación vigorosa. Valores bajos (marrón/blanco) indican suelo desnudo, agua o vegetación estresada.'),
            'ndwi': ('Índice de Agua (NDWI)', 'Valores altos (azul) indican presencia de agua o alta humedad. Valores bajos (rojo/amarillo) indican áreas secas.'),
            'nbr': ('Ratio de Quemado Normalizado (NBR)', 'Valores bajos indican áreas quemadas recientemente (pre-incendio vs post-incendio para dNBR). Este NBR simple puede correlacionarse con estrés hídrico o áreas quemadas.')
        }

        img_width = 6 * inch # Adjust as needed

        for key, (title, description) in available_maps.items():
            if key in image_paths and os.path.exists(image_paths[key]):
                story.append(Paragraph(f"<b>{title}</b>", styles['h2']))
                story.append(Spacer(1, 0.1*inch))
                story.append(Paragraph(description, styles['Normal']))
                story.append(Spacer(1, 0.2*inch))

                # Add image, handling potential size issues
                try:
                    img = Image(image_paths[key], width=img_width, height=img_width * 0.75) # Assume aspect ratio
                    img.hAlign = 'CENTER'
                    story.append(img)
                except Exception as img_err:
                    print(f"Error adding image {image_paths[key]} to PDF: {img_err}")
                    story.append(Paragraph(f"[Error al cargar imagen: {key}]", styles['Italic']))

                story.append(Spacer(1, 0.3*inch))
                # story.append(PageBreak()) # Add page break between maps if desired

            else:
                 print(f"Map image for {key} not found or path missing. Skipping in PDF.")


        # --- Footer/Disclaimer ---
        story.append(Spacer(1, 0.5*inch))
        disclaimer_style = styles['Italic']
        disclaimer_style.fontSize = 8
        story.append(Paragraph("Este es un informe generado automáticamente por GeoInforme Express MVP.", disclaimer_style))
        story.append(Paragraph("Los resultados son preliminares y dependen de la calidad y disponibilidad de las imágenes satelitales.", disclaimer_style))

        # Build the PDF
        doc.build(story)
        print(f"Successfully generated PDF: {pdf_filepath}")
        return pdf_filepath

    except Exception as e:
        print(f"ERROR generating PDF report: {e}")
        import traceback
        traceback.print_exc()
        return None