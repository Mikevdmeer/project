
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import os

if not os.path.exists('PDF_INVOICE'):
    os.makedirs('PDF_INVOICE')

tekst = input("Voer je tekst in: ")

pdf_bestand = canvas.Canvas("PDF_INVOICE/output.pdf", pagesize=A4)

pdf_bestand.drawString(100, 700, tekst)

pdf_bestand.save()

print("PDF is gegenereerd en opgeslagen in de PDF_INVOICE map.")