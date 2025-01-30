from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
import json
import os

def generate_invoice_pdf(json_file, output_file):
    # Load invoice data from JSON
    with open(json_file, 'r') as f:
        invoice_data = json.load(f)
    
    factuur = invoice_data['factuur']
    klant = factuur['klant']
    factuurregels = factuur['factuurregels']
    totalen = factuur['totalen']
    
    # Create PDF document
    doc = SimpleDocTemplate(output_file, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []
    
    # Title
    elements.append(Paragraph("Factuur", styles['Title']))
    elements.append(Spacer(1, 12))
    
    # Invoice details
    details = [
        ["Factuurnummer:", factuur['factuurnummer']],
        ["Factuurdatum:", factuur['factuurdatum']],
        ["Vervaldatum:", factuur['vervaldatum']],
        ["Ordernummer:", factuur['ordernummer']]
    ]
    table = Table(details, colWidths=[100, 200])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 5),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black)
    ]))
    elements.append(table)
    elements.append(Spacer(1, 12))
    
    # Customer details
    klant_info = f"Klant: {klant['naam']}<br/>Adres: {klant['adres']}<br/>E-mail: {klant['email']}"
    elements.append(Paragraph(klant_info, styles['Normal']))
    elements.append(Spacer(1, 12))
    
    # Invoice items
    table_data = [["Aantal", "Productnaam", "Prijs/stuk", "BTW%", "Subtotaal Excl. BTW", "BTW", "Subtotaal Incl. BTW"]]
    for item in factuurregels:
        table_data.append([
            item['aantal'],
            item['productnaam'],
            f"€ {item['prijs_per_stuk_excl_btw']:.2f}",
            f"{item['btw_percentage']}%",
            f"€ {item['subtotal_excl_btw']:.2f}",
            f"€ {item['btw_bedrag']:.2f}",
            f"€ {item['subtotal_incl_btw']:.2f}"
        ])
    
    invoice_table = Table(table_data, colWidths=[50, 150, 70, 50, 90, 70, 90])
    invoice_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 5),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black)
    ]))
    elements.append(invoice_table)
    elements.append(Spacer(1, 12))
    
    # Totals
    totals_data = [
        ["Totaal excl. BTW:", f"€ {totalen['totaal_excl_btw']:.2f}"],
        ["Totaal BTW:", f"€ {totalen['totaal_btw']:.2f}"],
        ["Totaal incl. BTW:", f"€ {totalen['totaal_incl_btw']:.2f}"]
    ]
    totals_table = Table(totals_data, colWidths=[150, 100])
    totals_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black)
    ]))
    elements.append(totals_table)
    
    # Build PDF
    doc.build(elements)
    print(f"Factuur opgeslagen als {output_file}")

# Voorbeeldgebruik
if __name__ == "__main__":
    input_json = "generated_invoices/invoice_example.json"  # Vervang dit met je echte JSON-bestand
    output_pdf = "factuur_output.pdf"
    generate_invoice_pdf(input_json, output_pdf)
