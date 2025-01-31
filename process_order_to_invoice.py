import json
import decimal
from decimal import Decimal
from datetime import datetime, timedelta
import os
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
import shutil

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
        print(f"Processing order {order_data['factuurnummer']}...")
        """Process order data into invoice data"""
        # Check if order is directly in data or nested under 'order'
        order = order_data.get('order', order_data.get('factuur'))
        
        if not order:
            raise KeyError("Could not find 'order' or 'factuur' in order data")
        
        # Calculate totals for each product
        product_lines = []
        for product in order.get('producten', []):
            # Calculate BTW percentage from BTW amount and price
            price = Decimal(str(product['prijs_per_stuk_excl_btw']))
            btw = Decimal(str(product.get('btw_per_stuk', 0)))
            btw_percentage = round((btw / price) * 100) if price else Decimal('21')
            
            # Create product with BTW percentage
            product_with_btw = {
                'productnaam': product['productnaam'],
                'aantal': product['aantal'],
                'prijs_per_stuk_excl_btw': price,
                'btw_percentage': btw_percentage
            }
            product_lines.append(self.calculate_line_totals(product_with_btw))
        
        # Calculate invoice totals
        total_excl_btw = sum(line['subtotal_excl_btw'] for line in product_lines)
        total_btw = sum(line['btw_bedrag'] for line in product_lines)
        total_incl_btw = sum(line['subtotal_incl_btw'] for line in product_lines)

        # Calculate due date
        vervaldatum = self.calculate_due_date(order['factuurdatum'], order.get('betaaltermijn', '30-dagen'))

        # Create invoice data structure
        invoice_data = {
            'factuur': {
                'factuurnummer': self.generate_invoice_number(order['factuurnummer']),
                'factuurdatum': order['factuurdatum'],
                'vervaldatum': vervaldatum,
                'ordernummer': order['factuurnummer'],
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

def process_orders(input_dir, output_dir, processed_dir, error_dir):
    """
    Process order files from input directory:
    - Generate invoice JSON files in output directory
    - Move processed order files to processed directory
    - Move error files to error directory
    """
    # Create directories if they don't exist
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(processed_dir, exist_ok=True)
    os.makedirs(error_dir, exist_ok=True)
    
    # Initialize invoice generator
    generator = InvoiceGenerator()
    
    # Process each JSON file in the input directory and its subdirectories
    for root, dirs, files in os.walk(input_dir):
        for filename in files:
            if filename.endswith('.json'):
                # Construct full paths
                input_path = os.path.join(root, filename)
                rel_path = os.path.relpath(root, input_dir)
                
                try:
                    # Read order data
                    with open(input_path, 'r', encoding='utf-8') as f:
                        order_data = json.load(f)
                    
                    # Validate order data
                    if not validate_order(order_data):
                        raise ValueError("Invalid order data structure")
                    
                    # Create output subdirectories
                    output_subdir = os.path.join(output_dir, rel_path)
                    processed_subdir = os.path.join(processed_dir, rel_path)
                    os.makedirs(output_subdir, exist_ok=True)
                    os.makedirs(processed_subdir, exist_ok=True)
                    
                    # Generate output paths
                    output_path = os.path.join(output_subdir, f"invoice_{filename}")
                    processed_path = os.path.join(processed_subdir, filename)
                    
                    # Generate invoice data
                    invoice_data = generator.process_order(order_data)
                    
                    # Save invoice data
                    with open(output_path, 'w', encoding='utf-8') as f:
                        json.dump(invoice_data, f, indent=2, ensure_ascii=False)
                    
                    # Move processed order file
                    shutil.move(input_path, processed_path)
                    
                    print(f"Successfully processed: {filename}")
                    
                except Exception as e:
                    print(f"Error processing {filename}: {str(e)}")
                    # Move error file to error directory
                    error_subdir = os.path.join(error_dir, rel_path)
                    os.makedirs(error_subdir, exist_ok=True)
                    error_path = os.path.join(error_subdir, filename)
                    shutil.move(input_path, error_path)

def validate_order(order_data):
    """Validate order data structure"""
    try:
        order = order_data['factuur']
        required_fields = [
            'factuurnummer',
            'factuurdatum',
            'betaaltermijn',
            'klant',
            'producten',
            'totaal_excl_btw',
            'totaal_btw',
            'totaal_incl_btw'
        ]
        
        for field in required_fields:
            if field not in order:
                return False
                
        if not isinstance(order['producten'], list):
            return False
            
        return True
        
    except (KeyError, TypeError):
        return False

def generate_invoice(order_data):
    """Generate invoice data from order data"""
    # Reuse existing invoice generation code
    order = order_data['factuur']
    
    # Calculate due date
    factuurdatum = datetime.strptime(order['factuurdatum'], '%d-%m-%Y')
    betaaltermijn = int(order['betaaltermijn'].split('-')[0])
    vervaldatum = (factuurdatum + timedelta(days=betaaltermijn)).strftime('%d-%m-%Y')
    
    # Create invoice structure
    invoice_data = {
        'factuur': {
            'factuurnummer': order['factuurnummer'],
            'factuurdatum': order['factuurdatum'],
            'vervaldatum': vervaldatum,
            'betaaltermijn': order['betaaltermijn'],
            'klant': order['klant'],
            'producten': order['producten'],
            'totaal_excl_btw': order['totaal_excl_btw'],
            'totaal_btw': order['totaal_btw'],
            'totaal_incl_btw': order['totaal_incl_btw']
        }
    }
    
    return invoice_data

class PDFGenerator:
    def __init__(self):
        print("Initializing PDFGenerator...")
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
            fontSize=9,
            spaceAfter=3
        )
        self.header_style = ParagraphStyle(
            'HeaderStyle',
            parent=self.styles['Heading1'],
            fontSize=12,
            spaceAfter=3
        )
        self.subheader_style = ParagraphStyle(
            'SubHeaderStyle',
            parent=self.styles['Heading2'],
            fontSize=10,
            spaceAfter=3
        )

    def create_header(self):
        print("Creating header...")
        logo_path = "afbeelding1.png"
        logo = Image(logo_path, width=100, height=100)
        
        company_info = [
            [logo],
            [Paragraph(self.company_info["name"], self.header_style)],
            [Paragraph(f"Adres: {self.company_info['address']}", self.custom_style)],
            [Paragraph(f"Postcode en plaats: {self.company_info['postal_city']}", self.custom_style)],
            [Paragraph(f"Telefoon: {self.company_info['phone']}", self.custom_style)]
        ]
        
        additional_info = [
            [Paragraph("", self.custom_style)],
            [Paragraph(f"KVK: {self.company_info['kvk']}", self.custom_style)],
            [Paragraph(f"BTW-Nummer: {self.company_info['btw']}", self.custom_style)],
            [Paragraph(f"E-mail: {self.company_info['email']}", self.custom_style)]
        ]
        
        header_table = Table([
            [Table(company_info, colWidths=[9*cm]), Table(additional_info, colWidths=[9*cm])]
        ])
        header_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        
        return [header_table, Spacer(1, 10)]

    def create_invoice_info(self, invoice_data):
        print(f"Creating invoice info for invoice {invoice_data['factuur']['factuurnummer']}...")
        invoice = invoice_data["factuur"]
        
        invoice_details = [
            [Paragraph("FACTUUR", self.subheader_style)],
            [Paragraph(f"Factuurnummer: {invoice['factuurnummer']}", self.custom_style)],
            [Paragraph(f"Factuurdatum: {invoice['factuurdatum']}", self.custom_style)],
            [Paragraph(f"Vervaldatum: {invoice['vervaldatum']}", self.custom_style)],
            [Paragraph(f"Ordernummer: {invoice['ordernummer']}", self.custom_style)]
        ]
        
        customer_details = [
            [Paragraph("KLANTGEGEVENS", self.subheader_style)],
            [Paragraph(f"Naam: {invoice['klant']['naam']}", self.custom_style)],
            [Paragraph(f"Adres: {invoice['klant']['adres']}", self.custom_style)],
            [Paragraph(f"{invoice['klant']['postcode']} {invoice['klant']['stad']}", self.custom_style)],
            [Paragraph(f"KVK-nummer: {invoice['klant']['KVK-nummer']}", self.custom_style)]
        ]
        
        info_table = Table([
            [Table(invoice_details, colWidths=[9*cm]), Table(customer_details, colWidths=[9*cm])]
        ])
        info_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        
        return [info_table, Spacer(1, 3)]

    def create_product_table(self, invoice_data):
        print(f"Creating product table with {len(invoice_data['factuur']['factuurregels'])} products...")
        # Aangepaste kolomnamen
        data = [['Beschrijving', 'Aantal', 'Eenheid', 'Tarief', 'BTW%', 'BTW', 'Totaal']]
        
        for product in invoice_data["factuur"]["factuurregels"]:
            data.append([
                product['productnaam'],
                str(product['aantal']),
                'Stuk',  # Toegevoegd eenheid kolom
                f"€{product['prijs_per_stuk_excl_btw']:.2f}",
                f"{product['btw_percentage']}%",
                f"€{product['btw_bedrag']:.2f}",
                f"€{product['subtotal_incl_btw']:.2f}"
            ])
        
        # Aangepaste kolombreedtes
        table = Table(data, colWidths=[6*cm, 2*cm, 2*cm, 2.5*cm, 1.5*cm, 2*cm, 2.5*cm])
        table.setStyle(TableStyle([
            # Lichtblauwe header (zoals in het voorbeeld)
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 4),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            # Lichtgrijze lijnen
            ('GRID', (0, 0), (-1, -1), 0.25, colors.lightgrey),
            ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),  # Rechtse uitlijning voor getallen
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),    # Linkse uitlijning voor beschrijving
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        
        return table

    def create_totals(self, invoice_data):
        print(f"Creating totals section. Total amount: €{invoice_data['factuur']['totalen']['totaal_incl_btw']:.2f}")
        totals = invoice_data["factuur"]["totalen"]
        
        # Aangepaste totalen layout
        totals_data = [
            ['Bedrag excl. BTW', f"€ {totals['totaal_excl_btw']:.2f}"],
            ['BTW', f"€ {totals['totaal_btw']:.2f}"],
            ['Totaalbedrag', f"€ {totals['totaal_incl_btw']:.2f}"]
        ]
        
        # Rechts uitgelijnde totalen tabel
        totals_table = Table(totals_data, colWidths=[12*cm, 6.5*cm])
        totals_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 2), (1, 2), 'Helvetica-Bold'),  # Laatste rij in bold
            ('TEXTCOLOR', (0, 2), (1, 2), colors.lightblue),  # Laatste rij in blauw
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        
        return [Spacer(1, 15), totals_table]

    def generate_pdf(self, json_data, output_path):
        print(f"\nGenerating PDF: {output_path}")
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=30,
            leftMargin=30,
            topMargin=30,
            bottomMargin=30
        )
        
        elements = []
        elements.extend(self.create_header())
        elements.extend(self.create_invoice_info(json_data))
        elements.append(self.create_product_table(json_data))
        elements.extend(self.create_totals(json_data))
        
        doc.build(elements)
        print(f"PDF generation completed: {output_path}\n")

def convert_invoices_to_pdf(input_dir, output_dir):
    """Convert all JSON invoices to PDF format"""
    print("\nStarting PDF conversion process...")
    print(f"Input directory: {input_dir}")
    print(f"Output directory: {output_dir}")
    
    pdf_generator = PDFGenerator()
    print("PDF Generator initialized successfully")
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    print(f"Ensured output directory exists: {output_dir}")
    
    # List all files in input directory
    files = os.listdir(input_dir)
    json_files = [f for f in files if f.endswith('.json')]
    print(f"Found {len(json_files)} JSON files to process")
    
    # Process each JSON file
    for filename in json_files:
        print(f"\nProcessing file: {filename}")
        input_path = os.path.join(input_dir, filename)
        output_path = os.path.join(output_dir, filename.replace('.json', '.pdf'))
        
        try:
            print(f"Reading JSON data from: {input_path}")
            # Read JSON data
            with open(input_path, 'r', encoding='utf-8') as f:
                invoice_data = json.load(f)
            print("JSON data loaded successfully")
            
            # Generate PDF
            print(f"Generating PDF: {output_path}")
            pdf_generator.generate_pdf(invoice_data, output_path)
            print(f"Successfully generated PDF for {filename}")
            
        except Exception as e:
            print(f"Error processing {filename}: {str(e)}")
            print(f"Error type: {type(e)}")
            import traceback
            print(f"Full traceback:\n{traceback.format_exc()}")

if __name__ == "__main__":
    # Directory paths
    base_dir = os.path.dirname(os.path.abspath(__file__))
    input_directory = os.path.join(base_dir, "generated_invoices")
    output_directory = os.path.join(base_dir, "generated_pdfs")
    
    print(f"\nScript starting...")
    print(f"Base directory: {base_dir}")
    print(f"Input directory: {input_directory}")
    print(f"Output directory: {output_directory}")
    
    # Convert invoices to PDF
    convert_invoices_to_pdf(input_directory, output_directory)