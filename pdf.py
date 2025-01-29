import pypdf
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import os

# Maak de directory aan als deze nog niet bestaat
if not os.path.exists('PDF_INVOICE'):
    os.makedirs('PDF_INVOICE')

# Vraag de gebruiker om tekst in te voeren
tekst = input("Voer je tekst in: ")

# Maak een nieuwe PDF met A4 formaat
pdf_bestand = canvas.Canvas("PDF_INVOICE/output.pdf", pagesize=A4)

# Voeg de tekst toe aan de PDF
# Positioneer de tekst op 100,700 (x,y coördinaten op de pagina)
pdf_bestand.drawString(100, 700, tekst)

# Sla de PDF op
pdf_bestand.save()

print("PDF is gegenereerd en opgeslagen in de PDF_INVOICE map.")
