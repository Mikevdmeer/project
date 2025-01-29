from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
import os

# Create directory if it doesn't exist
if not os.path.exists('PDF_INVOICE'):
    os.makedirs('PDF_INVOICE')

# Create PDF with A4 size
pdf_bestand = canvas.Canvas("PDF_INVOICE/output.pdf", pagesize=A4)

# Add invoice header
pdf_bestand.setFont("Helvetica-Bold", 16)
pdf_bestand.drawString(2*cm, 27*cm, "FACTUUR")

# Add date section
pdf_bestand.setFont("Helvetica-Bold", 12)
pdf_bestand.drawString(2*cm, 25*cm, "DATUM:")
pdf_bestand.setFont("Helvetica", 12)
pdf_bestand.drawString(2*cm, 24*cm, "Datum: 29-1-2025")

# Add invoice number
pdf_bestand.setFont("Helvetica-Bold", 12)
pdf_bestand.drawString(2*cm, 23*cm, "FACTUURNUMMER:")
pdf_bestand.setFont("Helvetica", 12)
pdf_bestand.drawString(2*cm, 22*cm, "Nummer: 2025-0001")

# Add company details
pdf_bestand.setFont("Helvetica-Bold", 12)
pdf_bestand.drawString(2*cm, 20*cm, "Appenheimers")
pdf_bestand.setFont("Helvetica", 12)
pdf_bestand.drawString(2*cm, 19*cm, "Adres: Romboutslaan 34")
pdf_bestand.drawString(2*cm, 18.5*cm, "Postcode en plaats: 3312 KP Dordrecht")
pdf_bestand.drawString(2*cm, 18*cm, "Telefoon: 06123456789")
pdf_bestand.drawString(2*cm, 17.5*cm, "KVK: 45398779")
pdf_bestand.drawString(2*cm, 17*cm, "BTW-Nummer: NL000099998B57")
pdf_bestand.drawString(2*cm, 16.5*cm, "E-mail: appenheimers@appenheimers.com")

# Add client details
pdf_bestand.setFont("Helvetica-Bold", 12)
pdf_bestand.drawString(2*cm, 14*cm, "FACTUUR AAN:")
pdf_bestand.setFont("Helvetica", 12)
pdf_bestand.drawString(2*cm, 13*cm, "Adres: Bagijnhof 10-12")
pdf_bestand.drawString(2*cm, 12.5*cm, "Postcode en plaats: 3311 KE Dordrecht")
pdf_bestand.drawString(2*cm, 12*cm, "Telefoon: 078 614 0828")
pdf_bestand.drawString(2*cm, 11.5*cm, "E-mail: Mcdonalds@happymeal.com")

# Save the PDF
pdf_bestand.save()

print("PDF is gegenereerd en opgeslagen in de PDF_INVOICE map.")
