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

# Production configuration
app.config['UPLOAD_DIR'] = 'uploads'
app.config['OUTPUT_DIR'] = 'generated'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure directories exist
os.makedirs(app.config['OUTPUT_DIR'], exist_ok=True)
os.makedirs(app.config['UPLOAD_DIR'], exist_ok=True)

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
    
    # Extract data from query parameters
    for key in ['voucher_number', 'passenger_names', 'check_in', 'check_out', 
                'length_of_stay', 'description', 'rate_incl', 'max_total']:
        data[key] = request.args.get(key, '')
    
    # Provide an auto-generated, editable invoice number to review form
    auto_inv = f"INV-{get_next_invoice_number()}"
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
    
    # Generate invoice PDF
    try:
        pdf_path = fill_invoice_template(invoice_data)
        return send_file(pdf_path, as_attachment=True, download_name=f"{invoice_data['invoice_number']}.pdf")
    except Exception as e:
        return f"Error generating invoice: {str(e)}", 500

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
    app.run(host='0.0.0.0', port=5000)
