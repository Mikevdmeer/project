import json
import decimal
from decimal import Decimal
from datetime import datetime, timedelta
import os

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

if __name__ == "__main__":
    input_directory = "test_set_softwareleverancier"
    output_directory = "generated_invoices"
    process_order_files(input_directory, output_directory)