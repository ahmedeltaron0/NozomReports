import pdfkit
from flask import render_template, make_response
import os
import uuid
import logging

# Configure PDF options
PDF_OPTIONS = {
    'page-size': 'A4',
    'margin-top': '0.75in',
    'margin-right': '0.75in',
    'margin-bottom': '0.75in',
    'margin-left': '0.75in',
    'encoding': "UTF-8",
    'no-outline': None,
    'quiet': ''
}


def generate_pdf(template_name, data, title="Report", orientation='portrait'):
    """
    Generate PDF from template with data

    Args:
        template_name (str): Name of the HTML template
        data (dict): Data to render in the template
        title (str): Title of the PDF document
        orientation (str): 'portrait' or 'landscape'

    Returns:
        Response: Flask response with PDF
    """
    try:
        # Add title to data
        data['pdf_title'] = title

        # Set orientation
        PDF_OPTIONS['orientation'] = orientation

        # Render HTML template
        html = render_template(template_name, **data)

        # Generate PDF
        pdf = pdfkit.from_string(html, False, options=PDF_OPTIONS)

        # Create response
        response = make_response(pdf)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'inline; filename="{title}_{uuid.uuid4().hex[:6]}.pdf"'

        return response

    except Exception as e:
        logging.exception("Error generating PDF")
        raise e