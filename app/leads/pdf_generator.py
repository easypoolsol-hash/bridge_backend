"""
PDF Generation for Lead Forms
Generates professional PDF documents for lead submissions
Following Fortune 500 best practices for document generation
"""

import io
from datetime import datetime
from django.template.loader import render_to_string
from weasyprint import HTML, CSS


def generate_lead_pdf(lead):
    """
    Generate PDF for a lead form submission

    Args:
        lead: Lead model instance

    Returns:
        bytes: PDF file content
    """
    # Prepare context for template
    context = {
        'lead': lead,
        'client': lead.client,
        'product': lead.product,
        'agent': lead.agent,
        'form_data': lead.form_data,
        'generated_at': datetime.now(),
    }

    # Render HTML template
    html_string = render_to_string('leads/pdf_template.html', context)

    # CSS for professional styling
    css_string = """
        @page {
            size: A4;
            margin: 2cm;
            @top-right {
                content: "Page " counter(page) " of " counter(pages);
                font-size: 9pt;
                color: #666;
            }
        }

        body {
            font-family: 'Helvetica', 'Arial', sans-serif;
            font-size: 11pt;
            line-height: 1.6;
            color: #333;
        }

        .header {
            text-align: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 2px solid #2196F3;
        }

        .header h1 {
            color: #2196F3;
            margin: 0;
            font-size: 24pt;
        }

        .header .reference {
            color: #666;
            font-size: 10pt;
            margin-top: 5px;
        }

        .section {
            margin-bottom: 25px;
            page-break-inside: avoid;
        }

        .section-title {
            background-color: #2196F3;
            color: white;
            padding: 8px 12px;
            margin-bottom: 15px;
            font-size: 12pt;
            font-weight: bold;
        }

        .info-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
            margin-bottom: 10px;
        }

        .info-item {
            margin-bottom: 10px;
        }

        .info-label {
            font-weight: bold;
            color: #666;
            font-size: 9pt;
            text-transform: uppercase;
            margin-bottom: 2px;
        }

        .info-value {
            font-size: 11pt;
            color: #333;
        }

        .form-field {
            margin-bottom: 12px;
            padding: 10px;
            background-color: #f5f5f5;
            border-left: 3px solid #2196F3;
        }

        .footer {
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            text-align: center;
            font-size: 8pt;
            color: #999;
            padding: 10px;
            border-top: 1px solid #ddd;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
        }

        th, td {
            padding: 8px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }

        th {
            background-color: #f5f5f5;
            font-weight: bold;
            color: #666;
        }
    """

    # Generate PDF
    html = HTML(string=html_string)
    css = CSS(string=css_string)

    # Return PDF as bytes
    pdf_bytes = html.write_pdf(stylesheets=[css])

    return pdf_bytes


def get_pdf_filename(lead):
    """
    Generate standardized PDF filename

    Args:
        lead: Lead model instance

    Returns:
        str: Filename for the PDF
    """
    # Format: LeadRef_ProductName_YYYYMMDD.pdf
    date_str = lead.created_at.strftime('%Y%m%d')
    product_slug = lead.product.name.replace(' ', '_')[:20]

    return f"{lead.reference_number}_{product_slug}_{date_str}.pdf"
