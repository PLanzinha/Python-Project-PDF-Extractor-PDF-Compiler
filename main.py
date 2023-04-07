import os
import pdfplumber
import fitz
from PIL import Image
import io
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Spacer

pdf_folder = 'pdfs'
images_folder = './pdfs/images'
output_text_file = 'compiled_text.txt'
output_links_file = 'extracted_links.txt'
merged_tables_pdf = 'merged_tables.pdf'

os.makedirs(images_folder, exist_ok=True)

compiled_text = []
extracted_links = []
tables_data = []


def extract_images(pdf_path, page_num, pdf_name):
    pdf_document = fitz.open(pdf_path)
    page = pdf_document.load_page(page_num)
    image_list = page.get_images(full=True)

    for img_index, img in enumerate(image_list):
        xref = img[0]
        base_image = pdf_document.extract_image(xref)
        img_bytes = base_image["image"]
        image = Image.open(io.BytesIO(img_bytes))
        image_ext = base_image["ext"]
        image_name = f"{pdf_name}_page{page_num + 1}_image{img_index + 1}.{image_ext}"
        image_path = os.path.join(images_folder, image_name)
        image.save(image_path)


def draw_tables_in_pdf(tables_data, output_pdf):
    doc = SimpleDocTemplate(output_pdf, pagesize=letter)
    elements = []

    for table_index, table in enumerate(tables_data):
        formatted_table = Table(table)
        formatted_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        elements.append(formatted_table)
        elements.append(Spacer(1, 0.2 * inch))

    doc.build(elements)


for pdf_file in os.listdir(pdf_folder):
    if pdf_file.endswith('.pdf') and os.path.isfile(os.path.join(pdf_folder, pdf_file)):
        pdf_path = os.path.join(pdf_folder, pdf_file)
        pdf_name = os.path.splitext(pdf_file)[0]

        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                tables = page.extract_tables()
                if tables:
                    tables_data.extend(tables)

                page_text = page.extract_text()
                if page_text:
                    compiled_text.append(page_text)

                extract_images(pdf_path, page_num, pdf_name)

        pdf_document = fitz.open(pdf_path)
        for page_num in range(pdf_document.page_count):
            page = pdf_document.load_page(page_num)
            links = page.get_links()
            for link in links:
                if 'uri' in link:
                    extracted_links.append(link['uri'])

with open(output_text_file, 'w', encoding='utf-8') as text_file:
    text_file.write('\n\n'.join(compiled_text))

with open(output_links_file, 'w', encoding='utf-8') as links_file:
    for link in extracted_links:
        links_file.write(link + '\n')

draw_tables_in_pdf(tables_data, merged_tables_pdf)

print("Extraction is complete, and files are ready!")
