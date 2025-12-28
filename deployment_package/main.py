from flask import Flask, request, render_template, send_file, redirect, url_for, send_from_directory, session
import datetime
import pdfkit
from pathlib import Path
from voucher_parser import parse_voucher_pdf
from invoice_generator import (
    fill_invoice_template,
    get_next_invoice_number
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
app.config['UPLOAD_DIR'] = 'uploads'
app.config['OUTPUT_DIR'] = 'generated'

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
    
    # Debug: Print the data being passed to template
    print("=== DEBUG: Data being passed to template ===")
    print(f"Data type: {type(data)}")
    if data:
        print(f"Data keys: {list(data.keys())}")
        print(f"Voucher number: {data.get('voucher_number', 'NOT FOUND')}")
        print(f"Passenger names: {data.get('passenger_names', 'NOT FOUND')}")
        print(f"Check-in: {data.get('check_in', 'NOT FOUND')}")
        print(f"Check-out: {data.get('check_out', 'NOT FOUND')}")
        print(f"Length of stay: {data.get('length_of_stay', 'NOT FOUND')}")
        print(f"Description: {data.get('description', 'NOT FOUND')}")
        print(f"Rate: {data.get('rate_incl', 'NOT FOUND')}")
        print(f"Total: {data.get('max_total', 'NOT FOUND')}")
    else:
        print("No data returned from parser")
    print("=== END DEBUG ===")
    
    # Provide an auto-generated, editable invoice number to review form
    auto_inv = f"INV-{get_next_invoice_number()}"
    return render_template('review.html', data=data, auto_invoice_number=auto_inv)

@app.route('/review')
def review():
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    """Review and edit parsed voucher data before generating invoice"""
    # Get data from query parameters
    data = {}
    for key in request.args:
        if key == 'auto_invoice_number':
            continue
        value = request.args.get(key)
        # Try to convert numeric values
        if key in ['qty', 'invoice_total', 'rate_incl', 'max_total', 'total_payment_received']:
            try:
                if value and value != 'N/A':
                    # Convert to float for numeric fields
                    if key in ['invoice_total', 'rate_incl', 'max_total', 'total_payment_received']:
                        data[key] = float(value)
                    else:
                        data[key] = int(value)
                else:
                    data[key] = 0 if key == 'qty' else 0.0
            except (ValueError, TypeError):
                data[key] = 0 if key == 'qty' else 0.0
        else:
            data[key] = value
    
    # Handle line items
    line_items = []
    idx = 0
    while f'description_{idx}' in request.args:
        if request.args.get(f'description_{idx}'):
            line_items.append({
                'description': request.args.get(f'description_{idx}', ''),
                'qty': int(request.args.get(f'qty_{idx}', 0)),
                'unit_price': float(request.args.get(f'unit_price_{idx}', 0)),
                'total': float(request.args.get(f'total_{idx}', 0))
            })
        idx += 1
    
    if line_items:
        data['line_items'] = line_items
    
    # Get auto invoice number
    auto_invoice_number = request.args.get('auto_invoice_number', f"INV-{get_next_invoice_number()}")
    
    return render_template('review.html', data=data, auto_invoice_number=auto_invoice_number)

@app.route('/debug-parser')
def debug_parser():
    """Debug route to test the voucher parser directly"""
    try:
        # Look for PDF files in the uploads directory
        uploads_dir = app.config['UPLOAD_DIR']
        if os.path.exists(uploads_dir):
            pdf_files = [f for f in os.listdir(uploads_dir) if f.endswith('.pdf')]
            if pdf_files:
                pdf_path = os.path.join(uploads_dir, pdf_files[0])
                print(f"Testing PDF parsing with: {pdf_path}")
                
                # Parse the PDF
                data = parse_voucher_pdf(pdf_path)
                
                if data:
                    return {
                        'status': 'success',
                        'message': 'PDF parsed successfully',
                        'data': data
                    }
                else:
                    return {
                        'status': 'error',
                        'message': 'Failed to parse PDF'
                    }
            else:
                return {
                    'status': 'error',
                    'message': 'No PDF files found in uploads directory'
                }
        else:
            return {
                'status': 'error',
                'message': 'Uploads directory not found'
            }
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Error: {str(e)}'
        }

@app.route('/manual-entry', methods=['GET', 'POST'])
def manual_entry():
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        data = {k: request.form[k] for k in request.form}
        
        # Calculate invoice total from manual entry
        invoice_total = 0.0
        
        # Add main charges (rate_incl * qty)
        if data.get('rate_incl') and data.get('qty'):
            try:
                rate = float(data['rate_incl'].replace('R', '').replace(',', '').strip())
                qty = int(data['qty'])
                main_total = rate * qty
                invoice_total += main_total
            except (ValueError, AttributeError):
                pass
        
        # Add ancillary charges
        if data.get('ancillary_charges'):
            try:
                ancillary_total = float(data['ancillary_charges'].replace('R', '').replace(',', '').strip())
                invoice_total += ancillary_total
            except (ValueError, AttributeError):
                pass
        
        # Create line items from manual entry
        line_items = []
        idx = 0
        while f'description_{idx}' in data:
            if data.get(f'description_{idx}'):  # Only add if description is not empty
                line_items.append({
                    'description': data.get(f'description_{idx}', ''),
                    'qty': int(data.get(f'qty_{idx}', 0)),
                    'unit_price': float(data.get(f'unit_price_{idx}', 0)),
                    'total': float(data.get(f'total_{idx}', 0))
                })
                try:
                    invoice_total += float(data.get(f'total_{idx}', 0))
                except Exception:
                    pass
            idx += 1
        
        # Process additional service details
        for i in range(5):
            service_desc = data.get(f'service_description_{i}', '').strip()
            if service_desc:
                try:
                    qty = int(data.get(f'service_qty_{i}', 1))
                    rate = float(data.get(f'service_rate_{i}', 0))
                    total = float(data.get(f'service_total_{i}', 0))
                    if total == 0:
                        total = qty * rate
                    
                    line_items.append({
                        'description': service_desc,
                        'qty': qty,
                        'unit_price': rate,
                        'total': total
                    })
                    invoice_total += total
                except (ValueError, TypeError):
                    pass
        
        # Process additional ancillary charges
        for i in range(5):
            ancillary_desc = data.get(f'ancillary_desc_{i}', '').strip()
            if ancillary_desc:
                try:
                    qty = int(data.get(f'ancillary_qty_{i}', 1))
                    amount = float(data.get(f'ancillary_amount_{i}', 0))
                    total = qty * amount
                    
                    line_items.append({
                        'description': ancillary_desc,
                        'qty': qty,
                        'unit_price': amount,
                        'total': total
                    })
                    invoice_total += total
                except (ValueError, TypeError):
                    pass
        
        # If no line items were entered, create default ones
        if not line_items:
            line_items = [
                {'description': 'Room Booking', 'qty': 1, 'unit_price': 500.00, 'total': 500.00}
            ]
            invoice_total = 500.00
        
        data['line_items'] = line_items
        data['invoice_total'] = invoice_total
        return redirect(url_for('review', **data))
    
    # Supply an auto-generated invoice number for manual entry form too
    auto_inv = f"INV-{get_next_invoice_number()}"
    # Provide an empty data object to avoid Jinja 'data is undefined' on GET
    return render_template('manual.html', auto_invoice_number=auto_inv, data={})

@app.route('/generate-invoice', methods=['POST'])
def generate_invoice():
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    data = {k: request.form[k] for k in request.form}
    
    # Extract only the required voucher fields and fallback to parsed fields for dynamic services
    voucher_data = {
        'check_in': data.get('check_in', ''),
        'check_out': data.get('check_out', ''),
        'length_of_stay': data.get('length_of_stay', ''),
        'voucher_number': data.get('voucher_number', ''),
        'passenger_names': data.get('passenger_names', ''),
        'description': data.get('description', ''),
        'uom': data.get('uom', ''),
        'qty': data.get('qty', ''),
        'currency_rate': data.get('currency_rate', ''),
        'rate_incl': data.get('rate_incl', ''),
        'max_total': data.get('max_total', ''),
        'ancillary_charges': data.get('ancillary_charges', ''),
        'ancillary_description': data.get('ancillary_description', ''),
        'total_payment_received': data.get('total_payment_received', '0.00'),
        'customer_name': data.get('passenger_names', ''),  # Use passenger names as customer name
        # Optional extras from forms
        'transport_rate': data.get('transport_rate', ''),
        'transport_total': data.get('transport_total', ''),
        'transport_description': data.get('transport_description', ''),
        'additional_service_desc': data.get('additional_service_desc', ''),
        'additional_service_qty': data.get('additional_service_qty', ''),
        'additional_service_rate': data.get('additional_service_rate', ''),
        'additional_service_total': data.get('additional_service_total', '')
    }

    # Collect all line items from the form (parser-provided plus any manually added via review/manual entry)
    parsed_line_items = []
    idx = 0
    while f'description_{idx}' in data:
        if data.get(f'description_{idx}'):
            parsed_line_items.append({
                'description': data.get(f'description_{idx}', ''),
                'qty': int(data.get(f'qty_{idx}', 0)),
                'unit_price': float(data.get(f'unit_price_{idx}', 0)),
                'total': float(data.get(f'total_{idx}', 0))
            })
        idx += 1
    
    # Calculate invoice total
    invoice_total = 0.0
    
    # Add main charges (rate_incl * qty)
    if voucher_data['rate_incl'] and voucher_data['qty']:
        try:
            rate = float(voucher_data['rate_incl'].replace('R', '').replace(',', '').strip())
            qty = int(voucher_data['qty'])
            main_total = rate * qty
            invoice_total += main_total
        except (ValueError, AttributeError):
            pass
    
    # Add ancillary charges (top-level field) if provided; otherwise rely on line items
    if voucher_data['ancillary_charges']:
        try:
            ancillary_total = float(voucher_data['ancillary_charges'].replace('R', '').replace(',', '').strip())
            invoice_total += ancillary_total
        except (ValueError, AttributeError):
            pass
    
    # Extract line items from review page (parser-provided + user-edited)
    line_items = parsed_line_items if parsed_line_items else []

    # Include any additional services/ancillary from manual-entry stage if present
    for i in range(5):
        service_desc = data.get(f'service_description_{i}', '').strip()
        if service_desc:
            try:
                qty = int(data.get(f'service_qty_{i}', 1))
                rate = float(data.get(f'service_rate_{i}', 0))
                total = float(data.get(f'service_total_{i}', 0)) or qty * rate
                line_items.append({'description': service_desc, 'qty': qty, 'unit_price': rate, 'total': total})
                invoice_total += total
            except (ValueError, TypeError):
                pass
    for i in range(5):
        ancillary_desc = data.get(f'ancillary_desc_{i}', '').strip()
        if ancillary_desc:
            try:
                qty = int(data.get(f'ancillary_qty_{i}', 1))
                amount = float(data.get(f'ancillary_amount_{i}', 0))
                total = qty * amount
                line_items.append({'description': ancillary_desc, 'qty': qty, 'unit_price': amount, 'total': total})
                invoice_total += total
            except (ValueError, TypeError):
                pass
    
    # Do not auto-add transport here to avoid duplication.
    # Transport will appear as a line item only if detected from the parsed voucher and shown in the form's line items.

    # Line items already include any added services; compute invoice_total from line_items for accuracy
    line_items = parsed_line_items if parsed_line_items else []

    # Combine voucher data with updated line items and provisional total
    invoice_data = {**voucher_data, 'line_items': line_items, 'invoice_total': invoice_total}

    # Determine invoice number: use edited value if provided, else auto-generate
    # Ensure INV- prefix is always present
    if data.get('invoice_number'):
        raw_inv = data.get('invoice_number').strip()
        inv_num = raw_inv if raw_inv.startswith('INV-') else f"INV-{raw_inv}"
    else:
        inv_num = f"INV-{get_next_invoice_number()}"

    # Always use HTML-to-PDF (wkhtmltopdf via pdfkit)
    today_str = datetime.datetime.now().strftime('%d %B %Y')

    # Compute payments and outstanding directly from invoice_total
    # Recompute invoice_total strictly from line items to avoid any drift
    try:
        computed_total = sum(float(item.get('total', 0)) for item in line_items)
    except Exception:
        computed_total = float(invoice_total)

    # Ensure invoice_total matches the actual sum of current line items
    invoice_data['invoice_total'] = computed_total

    try:
        payment_received = float(str(invoice_data.get('total_payment_received') or 0).replace('R', '').replace(',', '').strip())
    except Exception:
        payment_received = 0.0

    outstanding = max(0.0, float(computed_total) - payment_received)

    # Build absolute file URL for the logo (file:// URI) so wkhtmltopdf can load it
    logo_path = Path(os.getcwd()) / 'assets' / 'logo.png'
    logo_url = logo_path.resolve().as_uri()

    render_html = render_template(
        'invoice.html',
        data=invoice_data,
        invoice_number=inv_num,
        today=today_str,
        logo_file_url=logo_url,
        payment_received=payment_received,
        outstanding=outstanding
    )
    output_path = os.path.join(app.config['OUTPUT_DIR'], f"Invoice_{inv_num}.pdf")
    options = {
        'enable-local-file-access': None,
        'quiet': '',
        'page-size': 'A4',
        'margin-top': '5mm',
        'margin-bottom': '6mm',
        'margin-left': '8mm',
        'margin-right': '8mm',
        'encoding': 'UTF-8',
        'print-media-type': None,
        'dpi': 300,
        'zoom': '0.90',
        'page-height': '297mm',  # Explicit A4 height
        'page-width': '210mm'   # Explicit A4 width
    }
    try:
        pdfkit.from_string(render_html, output_path, options=options)
    except Exception as e:
        return ("PDF generation failed. Please ensure wkhtmltopdf is installed and accessible.\n"
                f"Error: {str(e)}", 500)
    return send_file(output_path, as_attachment=True)

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
                
                # Clean up temp file
                os.remove(temp_path)
                
                # Redirect to review page with extracted data for editing
                return redirect(url_for('review', **invoice_data))
                
            except Exception as e:
                # Clean up temp file on error
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                return f'Error parsing invoice: {str(e)}', 500
    
    # GET request - show upload form
    return render_template('edit_invoice.html')

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
            'has_ancillary_services': False
        }
        
        with pdfplumber.open(pdf_path) as pdf:
            text = ""
            for page in pdf.pages:
                text += page.extract_text() or ""
            
            # Extract invoice number
            inv_match = re.search(r'NO:\s*(INV-\d+)', text)
            if inv_match:
                invoice_data['voucher_number'] = inv_match.group(1)
            
            # Extract customer name - look for Guest Name field
            name_match = re.search(r'Guest Name:\s*(.+?)(?:\n|$)', text)
            if name_match:
                customer_name = name_match.group(1).strip()
                # Clean up any extra text that might have been captured
                if 'Check-in Date:' in customer_name:
                    customer_name = customer_name.split('Check-in Date:')[0].strip()
                invoice_data['customer_name'] = customer_name
                invoice_data['passenger_names'] = customer_name
            
            # Extract check-in/out dates
            checkin_match = re.search(r'Check-in Date:\s*(.+?)(?:\n|$)', text)
            if checkin_match:
                invoice_data['check_in'] = checkin_match.group(1).strip()
            
            checkout_match = re.search(r'Check-out Date:\s*(.+?)(?:\n|$)', text)
            if checkout_match:
                invoice_data['check_out'] = checkout_match.group(1).strip()
            
            # Extract length of stay
            stay_match = re.search(r'Length of Stay:\s*(\d+)\s*days', text)
            if stay_match:
                invoice_data['length_of_stay'] = stay_match.group(1)
            
            # Try to extract billing address if present
            billing_match = re.search(r'Billing Address:\s*(.+?)(?:\n|$)', text, re.DOTALL)
            if billing_match:
                billing_address = billing_match.group(1).strip()
                # Clean up multi-line addresses
                billing_address = ' '.join(billing_address.split())
                invoice_data['billing_address'] = billing_address
            
            # Extract line items from the services table - look for the actual table structure
            lines = text.split('\n')
            in_table = False
            table_started = False
            pending_text = []  # Buffer for description-only lines (no numbers)
            SERVICE_KEYWORDS = [
                "Accommodation", "Personal Services", "Laundry", "Transport", "Daily Transport", 
                "Meals", "Beverages", "Room Hire", "Equipment", "Sundries", "Telephone", "Internet",
                "Conference", "Training"
            ]
            
            for i, line in enumerate(lines):
                # Look for table header - be more flexible with header detection
                if ('Description' in line and 'Qty' in line and 'Price' in line and 'Total' in line) or \
                   ('Description' in line and 'Qty' in line and 'price' in line and 'total' in line) or \
                   ('Description' in line and 'Qty' in line and 'Rate' in line and 'Total' in line):
                    in_table = True
                    table_started = True
                    print(f"Found table header: {line}")
                    continue
                
                if in_table and line.strip():
                    # Skip empty lines and footer
                    line_stripped = line.strip()
                    if 'Total Amount Received' in line_stripped or 'Amount Due' in line_stripped or 'Payment Details' in line_stripped:
                        break
                    
                    # Ignore header-only or label lines (no digits and contains column keywords)
                    if not any(ch.isdigit() for ch in line_stripped):
                        lowered = line_stripped.lower()
                        if any(tok in lowered for tok in ['description','qty','quantity','unit','unit price','price','total','amount']):
                            continue
                    
                    # Robust pattern: Qty + Price + Total, supporting R/ZAR, spaces, commas, decimals
                    currency_pattern = r'(?:R|ZAR)?\s*(?:(?:\d{1,3}(?:[ ,]\d{3})+)(?:\.\d+)?|\d+(?:\.\d+)?)'
                    number_group_regex = f'(\\s+(\\d+)\\s+({currency_pattern})\\s+({currency_pattern}))'
                    matches = list(re.finditer(number_group_regex, line_stripped, re.IGNORECASE))
                    
                    if matches:
                        last_end = 0
                        for j, match in enumerate(matches):
                            try:
                                qty = int(match.group(2))
                                unit_price_str = match.group(3).upper().replace('R', '').replace('ZAR', '').replace(' ', '').replace(',', '')
                                total_str = match.group(4).upper().replace('R', '').replace('ZAR', '').replace(' ', '').replace(',', '')
                                unit_price = float(unit_price_str)
                                total = float(total_str)
                                
                                start = match.start()
                                description = line_stripped[last_end:start].strip()
                                
                                # If we have pending description-only text collected earlier, convert to a standalone item
                                if pending_text:
                                    cont = " ".join(pending_text).strip()
                                    if cont:
                                        invoice_data['line_items'].append({'description': cont, 'qty': 0, 'unit_price': 0.0, 'total': 0.0})
                                    pending_text = []
                                
                                # Split merged descriptions into separate items when a second service keyword appears mid-string
                                split_point = -1
                                for keyword in sorted(SERVICE_KEYWORDS, key=len, reverse=True):
                                    idx = description.lower().find(keyword.lower())
                                    if idx > 3:
                                        split_point = idx
                                        break
                                if split_point > 0:
                                    first_desc = description[:split_point].strip()
                                    second_desc = description[split_point:].strip()
                                    if first_desc:
                                        invoice_data['line_items'].append({'description': first_desc, 'qty': 0, 'unit_price': 0.0, 'total': 0.0})
                                    description = second_desc
                                
                                if description:
                                    line_item = {'description': description, 'qty': qty, 'unit_price': unit_price, 'total': total}
                                    invoice_data['line_items'].append(line_item)
                                    print(f"Added line item: {line_item}")
                                    
                                    if len(invoice_data['line_items']) == 1:
                                        invoice_data['description'] = description
                                        invoice_data['qty'] = qty
                                        invoice_data['rate_incl'] = unit_price
                                        invoice_data['max_total'] = total
                                        invoice_data['uom'] = 'Unit'
                                        invoice_data['currency_rate'] = 'ZAR'
                                        print(f"Set main service details: {description}, {qty}, {unit_price}, {total}")
                                
                                last_end = match.end()
                            except (ValueError, IndexError) as e:
                                print(f"Error parsing line item: {line_stripped}, Error: {e}")
                                continue
                        
                        # Any trailing text becomes pending for the next loop iteration
                        trailing = line_stripped[last_end:].strip()
                        if trailing:
                            pending_text.append(trailing)
                    else:
                        # No numeric group; collect as pending description-only text
                        pending_text.append(line_stripped)
            
            # After processing lines, flush any remaining pending description-only text as standalone items
            if pending_text:
                cont = " ".join(pending_text).strip()
                if cont:
                    invoice_data['line_items'].append({'description': cont, 'qty': 0, 'unit_price': 0.0, 'total': 0.0})
            
            # Calculate invoice total from line items
            invoice_data['invoice_total'] = sum(item['total'] for item in invoice_data['line_items'])
            
            normalized_items = []
            for item in invoice_data['line_items']:
                desc_lower = item.get('description', '').lower()
                if 'daily transport' in desc_lower and 'laundry' in desc_lower:
                    idx = desc_lower.find('daily transport')
                    transport_desc = item['description'][idx:].strip()
                    normalized_items.append({'description': 'Personal Services - Laundry', 'qty': 0, 'unit_price': 0.0, 'total': 0.0})
                    normalized_items.append({'description': transport_desc, 'qty': item.get('qty', 0), 'unit_price': item.get('unit_price', 0.0), 'total': item.get('total', 0.0)})
                else:
                    normalized_items.append(item)
            invoice_data['line_items'] = normalized_items
            
            # Extract payment received (look for "Total Amount Received")
            payment_match = re.search(r'Total Amount Received:\s*R?\s*([\d,]+\.?\d*)', text)
            if payment_match:
                payment_str = payment_match.group(1).replace(',', '')
                try:
                    invoice_data['total_payment_received'] = float(payment_str)
                except ValueError:
                    pass
            
            # Ensure numeric values are properly converted
            try:
                invoice_data['invoice_total'] = float(invoice_data['invoice_total'])
            except (ValueError, TypeError):
                invoice_data['invoice_total'] = 0.0
            
            try:
                invoice_data['total_payment_received'] = float(invoice_data['total_payment_received'])
            except (ValueError, TypeError):
                invoice_data['total_payment_received'] = 0.0
            
            # Extract voucher number if present
            voucher_match = re.search(r'Voucher:\s*(.+?)(?:\n|$)', text)
            if voucher_match:
                voucher = voucher_match.group(1).strip()
                if voucher != 'N/A':
                    invoice_data['voucher_number'] = invoice_data['voucher_number'] or voucher
            
            # Set default values for missing fields
            if not invoice_data['customer_name']:
                invoice_data['customer_name'] = 'Guest'
            if not invoice_data['voucher_number']:
                invoice_data['voucher_number'] = 'N/A'
            if not invoice_data['check_in']:
                invoice_data['check_in'] = 'N/A'
            if not invoice_data['check_out']:
                invoice_data['check_out'] = 'N/A'
            if not invoice_data['length_of_stay']:
                invoice_data['length_of_stay'] = '0'
            
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
            print(f"Line Items Count: {len(invoice_data['line_items'])}")
            print(f"Invoice Total: {invoice_data['invoice_total']}")
            print(f"Payment Received: {invoice_data['total_payment_received']}")
            print("=== END PARSED DATA ===")
            
            return invoice_data
            
    except Exception as e:
        raise Exception(f"Failed to parse invoice PDF: {str(e)}")

if __name__ == '__main__':
    os.makedirs(app.config['OUTPUT_DIR'], exist_ok=True)
    os.makedirs(app.config['UPLOAD_DIR'], exist_ok=True)
    app.run(debug=True)
