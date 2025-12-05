from flask import Flask, request, render_template, send_file, redirect, url_for, send_from_directory, session
import datetime
import pdfkit
from pathlib import Path
from voucher_parser import parse_voucher_pdf
from invoice_generator import (
    clean_pdf_text,
    get_next_invoice_number,
    cleanup_old_files
)
import os
import re
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__, static_folder='assets')
app.secret_key = 'ulendo_secret_key_2025'

# Jinja filter to format ZAR currency with space thousand separators
@app.template_filter('zar')
def format_zar(value):
    try:
        amount = float(value)
        formatted = f"{amount:,.2f}".replace(",", " ")
        return f"R {formatted}"
    except Exception:
        try:
            # Try to clean string inputs like 'R1234,56'
            s = str(value).replace('R', '').replace(',', '').strip()
            amount = float(s)
            formatted = f"{amount:,.2f}".replace(",", " ")
            return f"R {formatted}"
        except Exception:
            return f"R {value}"

# Application configuration moved to main execution block

@app.route('/')
def index():
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == 'info@ulendolodge.com' and password == 'Ulendo@#2025!':
            session['logged_in'] = True
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error='Invalid credentials')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route('/upload-voucher', methods=['POST'])
def upload_voucher():
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    file = request.files['voucher_pdf']
    if not file:
        return "No file uploaded", 400
    save_path = os.path.join(app.config['UPLOAD_DIR'], file.filename)
    file.save(save_path)
    data = parse_voucher_pdf(save_path)
    
    # Clean up the uploaded voucher immediately
    cleanup_old_files(app.config['UPLOAD_DIR'], days_old=0)
    
    # Provide an auto-generated, editable invoice number to review form
    auto_inv = get_next_invoice_number()
    return render_template('review.html', data=data, auto_invoice_number=auto_inv)

@app.route('/review')
def review():
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    """Review and edit parsed voucher data before generating invoice"""
    
    data = {}
    # Try to retrieve data from session first (for edit-invoice flow)
    if 'invoice_data_for_review' in session:
        # Change from pop() to get() to ensure data persists for potential multiple GET requests to /review
        data = session.get('invoice_data_for_review') 
        print(f"DEBUG: Retrieved invoice_data from session for review: {data.get('invoice_number_from_pdf', 'N/A')}")
    else:
        # Otherwise, extract data from query parameters (for upload-voucher or manual-entry flow)
        print("DEBUG: No invoice_data in session, retrieving from query parameters.")
        for key in ['voucher_number', 'passenger_names', 'check_in', 'check_out', 
                    'length_of_stay', 'description', 'rate_incl', 'max_total', 'invoice_total',
                    'total_payment_received', 'transport_rate', 'transport_total', 'transport_description',
                    'ancillary_charges', 'ancillary_description', 'has_transport', 'has_ancillary_services']:
            data[key] = request.args.get(key, '')
        
        # Reconstruct additional service line items if passed as indexed query params (from manual entry)
        manual_entry_line_items = []
        idx = 0
        while request.args.get(f'description_{idx}'):
            manual_entry_line_items.append({
                'description': request.args.get(f'description_{idx}', ''),
                'qty': int(request.args.get(f'qty_{idx}', 0)),
                'unit_price': float(request.args.get(f'unit_price_{idx}', 0)),
                'total': float(request.args.get(f'total_{idx}', 0))
            })
            idx += 1
        if manual_entry_line_items:
            data['line_items'] = manual_entry_line_items

        # Handle other indexed additional services from query params
        for i in range(5):
            desc = request.args.get(f'additional_service_desc_{i}', '')
            if desc:
                data[f'additional_service_desc_{i}'] = desc
                data[f'additional_service_qty_{i}'] = request.args.get(f'additional_service_qty_{i}', '')
                data[f'additional_service_rate_{i}'] = request.args.get(f'additional_service_rate_{i}', '')
                data[f'additional_service_total_{i}'] = request.args.get(f'additional_service_total_{i}', '')

    # The auto_invoice_number will always come from query parameters (either newly generated or extracted from PDF)
    auto_inv = request.args.get('auto_invoice_number', get_next_invoice_number())

    # If the retrieved data already has an invoice_number, prioritize it over auto_inv if auto_inv is a newly generated one.
    # This ensures that when editing, the original invoice number from the PDF is retained.
    if data.get('invoice_number_from_pdf') and not request.args.get('auto_invoice_number'):
        auto_inv = data['invoice_number_from_pdf']

    if auto_inv and not auto_inv.startswith('INV-'):
        auto_inv = f"INV-{auto_inv}"

    print(f"DEBUG: Final data sent to template in review route: {data}")
    print(f"DEBUG: Auto-invoice number sent to template: {auto_inv}")

    return render_template('review.html', data=data, auto_invoice_number=auto_inv)

@app.route('/generate-invoice', methods=['POST'])
def generate_invoice():
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    
    # Get form data
    invoice_data = {
        'invoice_number': request.form.get('invoice_number'),
        'customer_name': request.form.get('customer_name'),
        'voucher_number': request.form.get('voucher_number'),
        'check_in': request.form.get('check_in'),
        'check_out': request.form.get('check_out'),
        'length_of_stay': request.form.get('length_of_stay'),
        'description': request.form.get('description'),
        'qty': request.form.get('qty'),
        'rate_incl': request.form.get('rate_incl'),
        'max_total': request.form.get('max_total'),
        'uom': request.form.get('uom'),
        'currency_rate': request.form.get('currency_rate'),
        'invoice_total': request.form.get('max_total'),
        'total_payment_received': request.form.get('total_payment_received', 0),
        'line_items': []
    }
    
    # Determine invoice number: use edited value if provided, else auto-generate
    # Ensure INV- prefix is always present
    if request.form.get('invoice_number'):
        raw_inv = request.form.get('invoice_number').strip()
        inv_num = raw_inv if raw_inv.startswith('INV-') else f"INV-{raw_inv}"
    else:
        inv_num = f"INV-{get_next_invoice_number()}"
    
    # Add the determined invoice number to invoice_data for use in send_file
    invoice_data['invoice_number'] = inv_num

    # Always use HTML-to-PDF (wkhtmltopdf via pdfkit)
    today_str = datetime.datetime.now().strftime('%d %B %Y')

    # Recompute payments and outstanding directly from invoice_total to ensure consistency
    computed_total = sum(float(item.get('total', 0)) for item in invoice_data['line_items'])
    invoice_data['invoice_total'] = computed_total

    payment_received = float(str(invoice_data.get('total_payment_received') or 0).replace('R', '').replace(',', '').strip())
    outstanding = max(0.0, float(computed_total) - payment_received)

    # Build absolute file URL for the logo (file:// URI) so wkhtmltopdf can load it
    logo_path = Path(os.getcwd()) / 'assets' / 'logo.png'
    logo_file_url = logo_path.resolve().as_uri()

    # Render the HTML template
    rendered_html = render_template(
        'invoice.html',
        data=invoice_data,
        invoice_number=inv_num,
        today=today_str,
        logo_file_url=logo_file_url, # Changed from logo_url to logo_file_path
        payment_received=payment_received,
        outstanding=outstanding
    )

    # Define PDF options for wkhtmltopdf (to ensure single page and other settings)
    options = {
        'page-size': 'A4',
        'margin-top': '0mm',
        'margin-right': '0mm',
        'margin-bottom': '0mm',
        'margin-left': '0mm',
        'encoding': "UTF-8",
        'enable-local-file-access': None # Add this option
    }
    
    # Create the PDF file path
    pdf_filename = f"Invoice_{inv_num}.pdf"
    pdf_path = os.path.join(app.config['OUTPUT_DIR'], pdf_filename)

    # Convert HTML to PDF using pdfkit
    pdfkit.from_string(rendered_html, pdf_path, options=options)
    
    # Clean up generated invoices immediately
    cleanup_old_files(app.config['OUTPUT_DIR'], days_old=0)
    
    # Clear the invoice data from the session after use
    session.pop('invoice_data_for_review', None)

    return send_file(pdf_path, as_attachment=True, download_name=pdf_filename)

@app.route('/assets/<path:filename>')
def assets(filename):
    return send_from_directory('assets', filename)

@app.route('/generated/<path:filename>')
def generated_files(filename):
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    return send_from_directory('generated', filename)

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.config['UPLOAD_DIR'] = 'uploads'
    app.config['OUTPUT_DIR'] = 'generated'
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
    # Ensure directories exist
    os.makedirs(app.config['OUTPUT_DIR'], exist_ok=True)
    os.makedirs(app.config['UPLOAD_DIR'], exist_ok=True)
    app.run(host='0.0.0.0', port=5000)

def parse_existing_invoice(pdf_path):
    """Parse an existing invoice PDF to extract editable data"""
    try:
        import pdfplumber
        
        invoice_data = {
            'line_items': [],
            'invoice_total': 0.0,
            'total_payment_received': 0.0,
            'customer_name': '',
            'voucher_number': '',
            'check_in': '',
            'check_out': '',
            'length_of_stay': '',
            'passenger_names': '',
            'description': '',
            'uom': '',
            'currency_rate': '',
            'rate_incl': '',
            'max_total': '',
            'has_transport': False,
            'transport_description': '',
            'transport_rate': '',
            'transport_total': '',
            'has_ancillary_services': False,
            'ancillary_description': '',
            'ancillary_charges': '',
            'invoice_number_from_pdf': ''
        }
        
        with pdfplumber.open(pdf_path) as pdf:
            raw_text = ""
            for page in pdf.pages:
                # Accumulate text from each page, preserving original line breaks and adding a newline between pages
                raw_text += (page.extract_text(x_tolerance=1) or "") + "\n"
            
            # Apply comprehensive cleaning to the *entire* extracted text after all pages are processed
            from invoice_generator import clean_pdf_text
            cleaned_text = clean_pdf_text(raw_text)
            print(f"DEBUG: --- Cleaned PDF Text ---\n{cleaned_text}\n--- End Cleaned Text ---")

            # Extract invoice number (this is the document's own invoice number, e.g., INV-000602)
            # Use the cleaned_text for matching and flexible colon matching
            inv_num_match = re.search(r'NO\s*:\s*(INV-\d+)', cleaned_text, re.IGNORECASE)
            if inv_num_match:
                invoice_number_extracted = inv_num_match.group(1).strip()
                invoice_data['invoice_number_from_pdf'] = invoice_number_extracted
                print(f"DEBUG: Extracted Document Invoice Number: {invoice_number_extracted}")
            else:
                print(r"DEBUG: Document Invoice Number not found using pattern 'NO:\s*(INV-\d+)'")
                
                # Extract voucher number (e.g., G846886)
                # Adjusted regex to be less greedy and stop before "Check-in Date" or "Date:" or newline
                voucher_match_pdf = re.search(r'Voucher\s*:\s*([A-Z0-9]+)(?:\s+Check-in Date|\s+Date:|\n|$)', cleaned_text, re.IGNORECASE)
                if voucher_match_pdf:
                    invoice_data['voucher_number'] = voucher_match_pdf.group(1).strip()
                    print(f"DEBUG: Extracted Voucher Number: {invoice_data['voucher_number']}")
                else:
                    print(r"DEBUG: Voucher Number not found using pattern 'Voucher:\s*([A-Z0-9]+)'")

                # Extract customer name - look for Guest Name field with flexible colon matching
                # Make this regex non-greedy and stop at the next clear field or newline.
                name_match = re.search(r'Guest Name\s*:\s*(.+?)(?:\s*Check-out Date|\s*Check-in Date|\s*Date:|\s*Voucher:|\n|$)', cleaned_text, re.DOTALL | re.IGNORECASE)
                if name_match:
                    customer_name = name_match.group(1).strip()
                    invoice_data['customer_name'] = customer_name
                    invoice_data['passenger_names'] = customer_name
                    print(f"DEBUG: Extracted Customer Name: {invoice_data['customer_name']}")
                else:
                    print(r"DEBUG: Customer Name not found using pattern 'Guest Name:'")
                
                # Extract check-in/out dates with flexible colon matching
                checkin_match = re.search(r'Check-in Date\s*:\s*([\d/]+)', cleaned_text, re.IGNORECASE)
                if checkin_match:
                    invoice_data['check_in'] = checkin_match.group(1).strip()
                    print(f"DEBUG: Extracted Check-in Date: {invoice_data['check_in']}")
                else:
                    print(r"DEBUG: Check-in Date not found using pattern 'Check-in Date:'")
                
                checkout_match = re.search(r'Check-out Date\s*:\s*([\d/]+)', cleaned_text, re.IGNORECASE)
                if checkout_match:
                    invoice_data['check_out'] = checkout_match.group(1).strip()
                    print(f"DEBUG: Extracted Check-out Date: {invoice_data['check_out']}")
                else:
                    print(r"DEBUG: Check-out Date not found using pattern 'Check-out Date:'")
                
                # Extract length of stay - usually derived from dates, but can be explicit
                if invoice_data['check_in'] and invoice_data['check_out']:
                    try:
                        from datetime import datetime
                        check_in_date = datetime.strptime(invoice_data['check_in'], '%Y/%m/%d')
                        check_out_date = datetime.strptime(invoice_data['check_out'], '%Y/%m/%d')
                        length_of_stay = (check_out_date - check_in_date).days
                        invoice_data['length_of_stay'] = str(length_of_stay)
                        print(f"DEBUG: Calculated Length of Stay: {invoice_data['length_of_stay']}")
                    except ValueError:
                        print("DEBUG: Could not calculate length of stay from dates.")
                else:
                    # Fallback to direct extraction if calculation fails or dates are missing
                    stay_match = re.search(r'Length of Stay\s*:\s*(\d+)\s*days', cleaned_text, re.IGNORECASE)
                    if stay_match:
                        invoice_data['length_of_stay'] = stay_match.group(1).strip()
                        print(f"DEBUG: Extracted Length of Stay (fallback): {invoice_data['length_of_stay']}")
                    else:
                        print("DEBUG: Length of Stay not found via fallback pattern.")

                # Extract line items from the services table
                lines = cleaned_text.splitlines()
                in_table = False
                found_services_header = False
                table_end_patterns = [r'INVOICE TOTAL:', r'PAYMENT DETAILS', r'IMPORTANT NOTES', r'POLICIES & INFORMATION']

                print("DEBUG: Starting line item extraction...")
                # Keep track of where the header parsing starts
                header_search_start_line_idx = -1
                header_keywords_found = set() # To track 'Description', 'Qty', 'Unit Price', 'Total'

                for i, line in enumerate(lines):
                    line_stripped = line.strip()

                    if not found_services_header:
                        if re.search(r'SERVICES & CHARGES', line_stripped, re.IGNORECASE):
                            found_services_header = True
                            header_search_start_line_idx = i # Mark where to start looking for column headers
                            print(f"DEBUG: Found SERVICES & CHARGES header at line {i}: '{line_stripped}'")
                            continue # Move to the next line to find column headers

                    if found_services_header and not in_table:
                        # Within a few lines after SERVICES & CHARGES, look for column headers
                        # We will check for individual keywords across potentially multiple lines
                        if i <= header_search_start_line_idx + 4: # Look within the next 4 lines
                            if re.search(r'DESCRIPTION', line_stripped, re.IGNORECASE):
                                header_keywords_found.add('DESCRIPTION')
                            if re.search(r'QTY', line_stripped, re.IGNORECASE):
                                header_keywords_found.add('QTY')
                            if re.search(r'UNIT\s*PRICE', line_stripped, re.IGNORECASE):
                                header_keywords_found.add('UNIT PRICE')
                            elif re.search(r'PRICE', line_stripped, re.IGNORECASE) and 'UNIT PRICE' not in header_keywords_found: # Handle "PRICE" if "UNIT PRICE" not found
                                header_keywords_found.add('PRICE')
                            if re.search(r'TOTAL', line_stripped, re.IGNORECASE):
                                header_keywords_found.add('TOTAL')

                            # If all essential headers are found, we are in the table
                            if 'DESCRIPTION' in header_keywords_found and \
                               'QTY' in header_keywords_found and \
                               ('UNIT PRICE' in header_keywords_found or 'PRICE' in header_keywords_found) and \
                               'TOTAL' in header_keywords_found:
                                in_table = True
                                print(f"DEBUG: Found all table column headers. Starting line item parsing from line {i+1}")
                                continue # Continue to the next line, which should be the first line item
                        else:
                            # If we passed the header search window and didn't find them, something is wrong.
                            print("DEBUG: Exceeded header search window after SERVICES & CHARGES. Line item extraction aborted.")
                            found_services_header = False # Reset to prevent further header searching and the spurious debug message
                            continue # Continue to next line, not in table

                    if in_table and line_stripped:
                        # Check for table footer or end of relevant content for line items
                        if any(re.search(pattern, line_stripped, re.IGNORECASE) for pattern in table_end_patterns):
                            in_table = False # Exit table parsing mode
                            found_services_header = False # Also reset this to prevent spurious header search messages later
                            print(f"DEBUG: Found table footer/end content at line {i}: '{line_stripped}'")
                            continue # Continue to parse other sections like total/payment
                        
                        # Try to parse line item - more robust pattern after cleaning
                        # The description can be multi-word, then QTY, then R<PRICE>, then R<TOTAL>
                        # Example: Accommodation - Room booked , None . Rate includes Dinner , Breakfast & Lunch 21 R1688.50 R35458.50
                        line_item_match = re.search(r'(.+?)\s+(\d+)\s*R([\d.]+)\s*R([\d.]+)', line_stripped)
                        
                        if line_item_match:
                            try:
                                description = line_item_match.group(1).strip()
                                qty = int(line_item_match.group(2))
                                unit_price = float(line_item_match.group(3).replace(',', ''))
                                total = float(line_item_match.group(4).replace(',', ''))
                                
                                # Basic validation
                                if description and qty >= 0 and unit_price >= 0 and total >= 0:
                                    line_item = {
                                        'description': description,
                                        'qty': qty,
                                        'unit_price': unit_price,
                                        'total': total
                                    }
                                    invoice_data['line_items'].append(line_item)
                                    print(f"DEBUG: Successfully added line item: {line_item}")
                                    
                                    # Set main service details if this is the first item (for compatibility with review page structure)
                                    if not invoice_data.get('description'): # Only set if main description is not already set
                                        invoice_data['description'] = description
                                        invoice_data['qty'] = qty
                                        invoice_data['rate_incl'] = unit_price
                                        invoice_data['max_total'] = total
                                        invoice_data['uom'] = 'Unit' 
                                        invoice_data['currency_rate'] = 'ZAR'
                                        print(f"DEBUG: Set main service details from first item: {description}, {qty}, {unit_price}, {total}")
                            except (ValueError, IndexError) as e:
                                print(f"DEBUG: Error parsing line item '{line_stripped}': {e}")
                        else:
                            print(f"DEBUG: No line item match for line: '{line_stripped}'")
                
                # --- Post-table extraction (for totals and payments) ---
                # Recompute invoice total from line items (as a sanity check) 
                computed_invoice_total = sum(item.get('total', 0) for item in invoice_data['line_items'])
                print(f"DEBUG: Computed Invoice Total from line items (sanity check): {computed_invoice_total}")

                # Extract actual Invoice Total from the PDF text with flexible colon and currency symbol parsing
                invoice_total_match = re.search(r'INVOICE TOTAL\s*:\s*R\s*([\d,\s]+\.?\d*)', cleaned_text, re.IGNORECASE)
                if invoice_total_match:
                    extracted_total_str = invoice_total_match.group(1).replace(' ', '').replace(',', '')
                    try:
                        invoice_data['invoice_total'] = float(extracted_total_str)
                        print(f"DEBUG: Extracted Invoice Total from PDF: {invoice_data['invoice_total']}")
                    except ValueError:
                        print(f"DEBUG: Could not convert extracted Invoice Total '{extracted_total_str}' to float. Falling back to computed.")
                        invoice_data['invoice_total'] = computed_invoice_total # Fallback
                else:
                    print("DEBUG: Invoice Total not found using pattern 'INVOICE TOTAL:'. Falling back to computed.")
                    invoice_data['invoice_total'] = computed_invoice_total # Fallback
                
                # Payment Received logic: Since there's no explicit "Payment Received:" label in the provided PDF,
                # we will attempt to extract "Outstanding Balance:" and derive Payment Received.
                invoice_data['total_payment_received'] = 0.0 # Default to 0
                invoice_data['outstanding_balance'] = invoice_data['invoice_total'] # Default to invoice total

                outstanding_match = re.search(r'Outstanding Balance\s*:\s*R\s*([\d,\s]+\.?\d*)', cleaned_text, re.IGNORECASE)
                if outstanding_match:
                    outstanding_str = outstanding_match.group(1).replace(' ', '').replace(',', '')
                    try:
                        outstanding_balance = float(outstanding_str)
                        invoice_data['outstanding_balance'] = outstanding_balance
                        # Derive payment received: Invoice Total - Outstanding Balance
                        invoice_data['total_payment_received'] = max(0.0, invoice_data['invoice_total'] - outstanding_balance)
                        print(f"DEBUG: Extracted Outstanding Balance: {invoice_data['outstanding_balance']}")
                        print(f"DEBUG: Derived Payment Received: {invoice_data['total_payment_received']}")
                    except ValueError:
                        print(f"DEBUG: Could not convert extracted Outstanding Balance '{outstanding_str}' to float.")
                else:
                    print("DEBUG: Outstanding Balance not found. Payment Received defaults to 0 and Outstanding to Invoice Total.")

            # --- Populate specific fields from line_items for compatibility with review page form ---
            # These fields are expected by the review.html template for distinct services
            transport_found = False
            ancillary_found = False

            for item in list(invoice_data['line_items']): # Iterate over a copy to safely modify the original list if needed (though not needed for this fix)
                description = item['description'].lower()
                qty = item['qty']
                unit_price = item['unit_price']
                total = item['total']

                # Check for Main Accommodation service - should be the first item if present
                # And only if data.description is not already set from voucher_parser (for manual/upload flow)
                if not invoice_data.get('description') and ("accommodation" in description or "room booked" in description):
                    invoice_data['description'] = item['description']
                    invoice_data['qty'] = qty
                    invoice_data['rate_incl'] = unit_price
                    invoice_data['max_total'] = total
                    invoice_data['uom'] = 'Unit' 
                    invoice_data['currency_rate'] = 'ZAR'
                    print(f"DEBUG: Populated Main Accommodation Service: {item['description']}")

                # Check for Transport Services
                elif "transport" in description and not transport_found:
                    invoice_data['transport_description'] = item['description']
                    invoice_data['transport_rate'] = unit_price # Assuming unit price is the daily rate
                    invoice_data['transport_total'] = total
                    invoice_data['has_transport'] = True
                    transport_found = True
                    print(f"DEBUG: Populated Transport Services: {item['description']}")

                # Check for specific Ancillary Services (e.g., Laundry)
                elif "laundry" in description and not ancillary_found:
                    invoice_data['ancillary_description'] = item['description']
                    invoice_data['ancillary_charges'] = total # Assuming total for laundry is the charge
                    invoice_data['has_ancillary_services'] = True
                    ancillary_found = True
                    print(f"DEBUG: Populated Ancillary Services (Laundry): {item['description']}")
            
            # invoice_data['line_items'] now correctly contains all items initially parsed. No need to clear or reassign.
            # No longer need to populate indexed additional services, as they should now be in final_line_items
            # Remove the loop that populated invoice_data[f'additional_service_desc_{idx}'] etc. here
            # This was causing issues with the template expecting *new* entries.

            # Debug output
            print("=== PARSED INVOICE DATA ===")
            print(f"Customer Name: {invoice_data['customer_name']}")
            print(f"Voucher Number: {invoice_data['voucher_number']}")
            print(f"Check-in: {invoice_data['check_in']}")
            print(f"Check-out: {invoice_data['check_out']}")
            print(f"Length of Stay: {invoice_data['length_of_stay']}")
            print(f"Description: {invoice_data.get('description', 'N/A')}")
            print(f"Rate: {invoice_data.get('rate_incl', 'N/A')}")
            print(f"Total: {invoice_data.get('max_total', 'N/A')}")
            print(f"Has Transport: {invoice_data.get('has_transport', False)}")
            print(f"Transport Description: {invoice_data.get('transport_description', 'N/A')}")
            print(f"Transport Rate: {invoice_data.get('transport_rate', 'N/A')}")
            print(f"Transport Total: {invoice_data.get('transport_total', 'N/A')}")
            print(f"Has Ancillary Services: {invoice_data.get('has_ancillary_services', False)}")
            print(f"Ancillary Description: {invoice_data.get('ancillary_description', 'N/A')}")
            print(f"Ancillary Charges: {invoice_data.get('ancillary_charges', 'N/A')}")
            print(f"Line Items Count (generic): {len(invoice_data['line_items'])}")
            for item in invoice_data['line_items']:
                print(f"  - {item['description']}: Qty {item['qty']}, Unit Price {item['unit_price']:.2f}, Total {item['total']:.2f}")
            print(f"Invoice Total: {invoice_data['invoice_total']}")
            print(f"Payment Received: {invoice_data['total_payment_received']}")
            print("=== END PARSED DATA ===")
            
            return invoice_data
            
    except Exception as e:
        raise Exception(f"Failed to parse invoice PDF: {str(e)}")

@app.route('/edit-invoice', methods=['GET', 'POST'])
def edit_invoice():
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        if 'invoice_pdf' not in request.files:
            return 'No file uploaded', 400
        
        file = request.files['invoice_pdf']
        if file.filename == '':
            return 'No file selected', 400
        
        if file and file.filename.endswith('.pdf'):
            # Save the uploaded PDF temporarily
            temp_path = os.path.join(app.config['UPLOAD_DIR'], 'temp_invoice.pdf')
            file.save(temp_path)
            
            try:
                # Parse the existing invoice PDF to extract data
                invoice_data = parse_existing_invoice(temp_path)
                
                # Store the entire invoice_data in session for the review page
                session['invoice_data_for_review'] = invoice_data

                # Clean up temp file
                os.remove(temp_path)
                
                # Redirect to review page. Only pass auto_invoice_number as query param
                # The rest of the data will be retrieved from the session on the review page.
                auto_inv_num_param = invoice_data.get('invoice_number_from_pdf', '')
                return redirect(url_for('review', auto_invoice_number=auto_inv_num_param))
                
            except Exception as e:
                # Clean up temp file on error
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                return f'Error parsing invoice: {str(e)}', 500
    
    # GET request - show upload form
    return render_template('edit_invoice.html')
