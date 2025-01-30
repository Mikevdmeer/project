import json
import decimal
from decimal import Decimal
from datetime import datetime, timedelta
import os
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm

class BTWCalculator:
    @staticmethod
    def round_btw(amount):
        """
        Round BTW amount according to Belastingdienst rules:
        - Round down for amounts ending in .5
        - Normal rounding for all other amounts
        """
        # Convert to Decimal for precise calculation
        dec = Decimal(str(amount))
        # Get cents part
        cents = dec * 100 % 100
        
        if cents == Decimal('50'):
            return Decimal(str(int(dec)))
        return dec.quantize(Decimal('0.01'), rounding=decimal.ROUND_HALF_UP)

class InvoiceGenerator:
    def __init__(self):
        self.current_year = datetime.now().year

    def generate_invoice_number(self, order_number):
        """Generate invoice number based on order number"""
        return f"F-{order_number}"

    def calculate_due_date(self, order_date, payment_term):
        """Calculate due date based on order date and payment term"""
        date_obj = datetime.strptime(order_date, "%d-%m-%Y")
        days = int(payment_term.split('-')[0])
        return (date_obj + timedelta(days=days)).strftime("%d-%m-%Y")

    def calculate_line_totals(self, product):
        """Calculate totals for a single product line"""
        aantal = Decimal(str(product['aantal']))
        price = Decimal(str(product['prijs_per_stuk_excl_btw']))
        btw_percentage = Decimal(str(product['btw_percentage']))

        subtotal_excl = aantal * price
        btw_amount = BTWCalculator.round_btw(subtotal_excl * btw_percentage / 100)
        subtotal_incl = subtotal_excl + btw_amount

        return {
            'aantal': int(aantal),
            'productnaam': product['productnaam'],
            'prijs_per_stuk_excl_btw': float(price),
            'btw_percentage': int(btw_percentage),
            'subtotal_excl_btw': float(subtotal_excl),
            'btw_bedrag': float(btw_amount),
            'subtotal_incl_btw': float(subtotal_incl)
        }

    def process_order(self, order_data):
        """Process order data into invoice data"""
        order = order_data['order']
        
        # Calculate totals for each product
        product_lines = [self.calculate_line_totals(product) for product in order['producten']]
        
        # Calculate invoice totals
        total_excl_btw = sum(line['subtotal_excl_btw'] for line in product_lines)
        total_btw = sum(line['btw_bedrag'] for line in product_lines)
        total_incl_btw = sum(line['subtotal_incl_btw'] for line in product_lines)

        # Calculate due date
        vervaldatum = self.calculate_due_date(order['orderdatum'], order['betaaltermijn'])

        # Create invoice data structure
        invoice_data = {
            'factuur': {
                'factuurnummer': self.generate_invoice_number(order['ordernummer']),
                'factuurdatum': order['orderdatum'],
                'vervaldatum': vervaldatum,
                'ordernummer': order['ordernummer'],
                'klant': order['klant'],
                'factuurregels': product_lines,
                'totalen': {
                    'totaal_excl_btw': round(total_excl_btw, 2),
                    'totaal_btw': round(total_btw, 2),
                    'totaal_incl_btw': round(total_incl_btw, 2)
                }
            }
        }

        return invoice_data

def process_order_files(input_dir, output_dir):
    """Process all order files in the input directory"""
    generator = InvoiceGenerator()
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Process each JSON file in the input directory
    for filename in os.listdir(input_dir):
        if filename.endswith('.json'):
            input_path = os.path.join(input_dir, filename)
            output_path = os.path.join(output_dir, f"invoice_{filename}")

            try:
                # Read order data
                with open(input_path, 'r', encoding='utf-8') as f:
                    order_data = json.load(f)

                # Generate invoice data
                invoice_data = generator.process_order(order_data)

                # Save invoice data
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(invoice_data, f, indent=2, ensure_ascii=False)
                
                print(f"Processed {filename} successfully")

            except Exception as e:
                print(f"Error processing {filename}: {str(e)}")

class PDFGenerator:
    def __init__(self):
        self.company_info = {
            "name": "Appenheimers",
            "address": "Romboutslaan 34",
            "postal_city": "3312 KP Dordrecht",
            "phone": "06123456789",
            "kvk": "45398779",
            "btw": "NL000099998B57",
            "email": "appenheimers@appenheimers.com"
        }
        self.styles = getSampleStyleSheet()
        self.custom_style = ParagraphStyle(
            'CustomStyle',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=12
        )

    def create_header(self):
        elements = []
        # Company info
        elements.append(Paragraph(self.company_info["name"], self.styles["Heading1"]))
        elements.append(Paragraph(f"Adres: {self.company_info['address']}", self.custom_style))
        elements.append(Paragraph(f"Postcode en plaats: {self.company_info['postal_city']}", self.custom_style))
        elements.append(Paragraph(f"Telefoon: {self.company_info['phone']}", self.custom_style))
        elements.append(Paragraph(f"KVK: {self.company_info['kvk']}", self.custom_style))
        elements.append(Paragraph(f"BTW-Nummer: {self.company_info['btw']}", self.custom_style))
        elements.append(Paragraph(f"E-mail: {self.company_info['email']}", self.custom_style))
        elements.append(Spacer(1, 20))
        return elements

    def create_invoice_info(self, invoice_data):
        elements = []
        invoice = invoice_data["factuur"]
        
        # Invoice details
        elements.append(Paragraph("FACTUUR", self.styles["Heading2"]))
        elements.append(Paragraph(f"Factuurnummer: {invoice['factuurnummer']}", self.custom_style))
        elements.append(Paragraph(f"Factuurdatum: {invoice['factuurdatum']}", self.custom_style))
        elements.append(Paragraph(f"Vervaldatum: {invoice['vervaldatum']}", self.custom_style))
        elements.append(Paragraph(f"Ordernummer: {invoice['ordernummer']}", self.custom_style))
        elements.append(Spacer(1, 20))

        # Customer info
        elements.append(Paragraph("KLANTGEGEVENS", self.styles["Heading3"]))
        elements.append(Paragraph(f"Naam: {invoice['klant']['naam']}", self.custom_style))
        elements.append(Paragraph(f"Adres: {invoice['klant']['adres']}", self.custom_style))
        elements.append(Paragraph(f"Postcode: {invoice['klant']['postcode']}", self.custom_style))
        elements.append(Paragraph(f"Stad: {invoice['klant']['stad']}", self.custom_style))
        elements.append(Paragraph(f"KVK-nummer: {invoice['klant']['KVK-nummer']}", self.custom_style))
        elements.append(Spacer(1, 20))
        
        return elements

    def create_product_table(self, invoice_data):
        # Table header
        data = [['Product', 'Aantal', 'Prijs (excl. BTW)', 'BTW %', 'BTW bedrag', 'Totaal (incl. BTW)']]
        
        # Add products
        for product in invoice_data["factuur"]["factuurregels"]:
            data.append([
                product['productnaam'],
                str(product['aantal']),
                f"€ {product['prijs_per_stuk_excl_btw']:.2f}",
                f"{product['btw_percentage']}%",
                f"€ {product['btw_bedrag']:.2f}",
                f"€ {product['subtotal_incl_btw']:.2f}"
            ])
        
        # Create table
        table = Table(data, colWidths=[7*cm, 2*cm, 3*cm, 2*cm, 2.5*cm, 3*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
        ]))
        
        return table

    def create_totals(self, invoice_data):
        elements = []
        totals = invoice_data["factuur"]["totalen"]
        
        elements.append(Spacer(1, 20))
        elements.append(Paragraph(f"Totaal exclusief BTW: € {totals['totaal_excl_btw']:.2f}", self.styles["Normal"]))
        elements.append(Paragraph(f"BTW: € {totals['totaal_btw']:.2f}", self.styles["Normal"]))
        elements.append(Paragraph(f"Totaal inclusief BTW: € {totals['totaal_incl_btw']:.2f}", self.styles["Heading3"]))
        
        return elements

    def generate_pdf(self, json_data, output_path):
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        elements = []
        elements.extend(self.create_header())
        elements.extend(self.create_invoice_info(json_data))
        elements.append(self.create_product_table(json_data))
        elements.extend(self.create_totals(json_data))
        
        doc.build(elements)

def convert_invoices_to_pdf(input_dir, output_dir):
    """Convert all JSON invoices to PDF format"""
    pdf_generator = PDFGenerator()
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Process each JSON file
    for filename in os.listdir(input_dir):
        if filename.endswith('.json'):
            input_path = os.path.join(input_dir, filename)
            output_path = os.path.join(output_dir, filename.replace('.json', '.pdf'))
            
            try:
                # Read JSON data
                with open(input_path, 'r', encoding='utf-8') as f:
                    invoice_data = json.load(f)
                
                # Generate PDF
                pdf_generator.generate_pdf(invoice_data, output_path)
                print(f"Generated PDF for {filename}")
                
            except Exception as e:
                print(f"Error processing {filename}: {str(e)}")

if __name__ == "__main__":
    input_directory = "test_set_softwareleverancier"
    output_directory = "generated_invoices"
    process_order_files(input_directory, output_directory)
    convert_invoices_to_pdf(output_directory, "generated_pdfs")
