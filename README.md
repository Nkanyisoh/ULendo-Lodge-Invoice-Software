<<<<<<< HEAD
# Ulendo Lodge Invoice Generator

A Flask-based web application for generating professional invoices from voucher PDFs.

## Features

- **PDF Voucher Parsing**: Extract data from voucher PDFs using PyPDF2
- **Invoice Generation**: Create professional PDF invoices with company branding
- **Web Interface**: User-friendly web interface for uploading and processing vouchers
- **Manual Entry**: Option to manually enter invoice details
- **Professional Design**: Modern, professional invoice design with company branding

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd UlendoInvoiceApp
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Install wkhtmltopdf** (required for PDF generation):
   - **Windows**: Download from https://wkhtmltopdf.org/downloads.html
   - **macOS**: `brew install wkhtmltopdf`
   - **Linux**: `sudo apt-get install wkhtmltopdf`

## Usage

### 1. Start the Application

```bash
python main.py
```

The application will be available at `http://localhost:5000`

### 2. Upload Voucher PDF

1. Go to the web interface
2. Click "Choose PDF File" and select your voucher PDF
3. Click "Process Voucher"
4. Review the extracted data
5. Generate the invoice

### 3. Test the Parser

To test the PDF parser independently:

```bash
python test_parser.py
```

This will test the parser with any PDF files in the `uploads/` directory.

### 4. Manual Entry

If you prefer to enter invoice details manually:
1. Click "Enter Manually" on the main page
2. Fill in all required fields
3. Generate the invoice

## File Structure

```
UlendoInvoiceApp/
├── main.py                 # Flask application
├── voucher_parser.py       # PyPDF2-based PDF parser
├── invoice_generator.py    # Invoice generation functions
├── templates/              # HTML templates
│   ├── index.html         # Main page
│   ├── review.html        # Data review page
│   └── invoice.html       # Invoice template
├── uploads/               # PDF upload directory
├── generated/             # Generated invoice directory
├── assets/                # Static assets (CSS, images)
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

## PDF Parser

The new `voucher_parser.py` uses PyPDF2 for more reliable text extraction and includes:

- **Structured Data Extraction**: Organized extraction of voucher information
- **Regex-based Parsing**: Robust pattern matching for various voucher formats
- **Multiple Format Support**: Handles different voucher layouts
- **Invoice Format Conversion**: Converts parsed data to invoice format

### Supported Data Fields

- Voucher number
- Passenger information
- Check-in/check-out dates
- Length of stay
- Room details and rates
- Ancillary charges
- Meal plans
- Company information
- Billing details

## Invoice Template

The invoice template (`templates/invoice.html`) features:

- **Professional Design**: Modern, clean layout
- **Company Branding**: Ulendo Lodge logo and colors
- **Responsive Layout**: Optimized for PDF generation
- **Single Page**: Designed to fit on one page
- **Semantic UI**: Card-based design elements

## Configuration

### Environment Variables

Create a `.env` file in the root directory:

```env
UPLOAD_DIR=uploads
OUTPUT_DIR=generated
```

### PDF Generation Options

PDF generation options can be configured in `main.py`:

```python
pdfkit_options = {
    'page-size': 'A4',
    'margin-top': '3mm',
    'margin-bottom': '3mm',
    'margin-left': '3mm',
    'margin-right': '3mm',
    'encoding': 'UTF-8',
    'no-outline': None,
    'disable-smart-shrinking': None
}
```

## Troubleshooting

### Common Issues

1. **PDF Generation Fails**:
   - Ensure wkhtmltopdf is installed and in PATH
   - Check that the HTML template is valid
   - Verify all required data is present

2. **Parser Not Extracting Data**:
   - Check PDF format compatibility
   - Verify PDF is not password-protected
   - Test with `test_parser.py`

3. **Invoice Layout Issues**:
   - Check CSS compatibility with wkhtmltopdf
   - Verify page size and margin settings
   - Test with different content lengths

### Debug Mode

Enable debug mode by setting:

```python
app.debug = True
```

## Development

### Adding New Voucher Formats

1. Update regex patterns in `voucher_parser.py`
2. Add new field mappings in `convert_to_invoice_format()`
3. Test with sample PDFs

### Customizing Invoice Design

1. Modify `templates/invoice.html`
2. Update CSS styles
3. Test PDF generation

### Extending Functionality

1. Add new routes in `main.py`
2. Create new templates
3. Update data models as needed

## License

This project is proprietary software for Ulendo Lodge.

## Support

For technical support or questions, contact the development team.
=======
# ULendo-Lodge-Invoice-Software
Software for Generating Invoices
>>>>>>> 88b1cee439e83070fe4a7822d5e3cf29983ed3f3
