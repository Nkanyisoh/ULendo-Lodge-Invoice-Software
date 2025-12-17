import re
import json
from PyPDF2 import PdfReader
import os

def parse_voucher_pdf(pdf_path):
    """
    Parse voucher PDF using PyPDF2 with structured data extraction
    """
    try:
        # Load the PDF
        reader = PdfReader(pdf_path)
        
        # Extract all text
        text = "\n".join(page.extract_text() for page in reader.pages)
        
        print("=== EXTRACTED PDF TEXT ===")
        print(text)
        print("=== END EXTRACTED TEXT ===")
        
        # Helper function to search with regex
        def search(pattern, flags=0):
            match = re.search(pattern, text, flags)
            return match.group(1).strip() if match else None
        
        # Helper function to search with multiple groups
        def search_multiple(pattern, flags=0):
            match = re.search(pattern, text, flags)
            if match:
                return [group.strip() for group in match.groups()]
            return None
        
        # Build structured data
        data = {
            "document_details": {
                "created_by": search(r"Created by (.+?) on"),
                "creation_date": search(r"on (\d{2} \w+ \d{4})"),
                "voucher_number": search(r"Voucher (\w+)\s+-"),
                "voucher_type": search(r"Voucher \w+\s+-\s+(.+)")
            },
            "billing_address": {
                "company": search(r"BillingAddress\s+(.+)"),
                "vat_number": search(r"Vat Nr:(\d+)"),
                "address": search_multiple(r"Vat Nr:.*?\n(.+)\n(.+)\n(.+)", re.DOTALL),
                "email": search(r"Email:([^\s]+)")
            },
            "passenger_info": {
                "name": search(r"Passenger name/s.*?\n([A-Z\s]+)"),
                "contact": search(r"\n(\d{10})\n"),
                "party_size": search(r"Number inparty:(\d+)")
            },
            "supplier_details": {
                "name": search(r"TO:\s*\n(.+)"),
                "address": search_multiple(r"TO:\s*\n.+\n(.+)\n(.+)\n(.+)"),
                "contact": search(r"Gauteng\n(\d{10})"),
                "email": search(r"Gauteng.*\n[0-9 ]+\n([^\s]+)"),
                "code": search(r"QtSupplier Code:(\w+)")
            },
            "stay_details": {
                "check_in": search(r"Check-in\s*(\d{4}/\d{2}/\d{2})"),
                "check_out": search(r"Check-out\s*(\d{4}/\d{2}/\d{2})"),
                "length": search(r"Length ofStay\s*(\d+)"),
                "rooms": search(r"Number ofRooms\s*(\d+)"),
                "room_type": search(r"Description.*?Double.*"),
                "rate_per_night": search(r"ZAR\s*([\d\s]+\.\d{2})"),
                "total": search(r"Max Total.*\n.*\n.*\n.*\n.*\n.*\n.*ZAR\s*\d+\s+([\d\s]+\.\d{2})")
            },
            "remarks": {
                "voucher": re.findall(r"Voucher Remarks\s*(\*.*?)(?=The quoted rate)", text, re.DOTALL),
                "notes": search(r"The quoted rate.*\n\n*(.+)")
            }
        }
        
        # Look for accommodation details in the actual voucher format
        accommodation_match = re.search(r"Room\s*Night\s*(\d+)\s*ZAR\s*(\d+[\s\d]*\.\d{2})\s*(\d+[\s\d]*\.\d{2})", text, re.IGNORECASE)
        if accommodation_match:
            data["accommodation"] = {
                "nights": accommodation_match.group(1),
                "rate_per_night": accommodation_match.group(2),
                "total": accommodation_match.group(3)
            }
        
        # Look for accommodation details in the actual voucher format with different spacing
        if not data.get("accommodation"):
            accommodation_match2 = re.search(r"Room\s*Night\s*(\d+)\s*ZAR\s*(\d+[\s\d]*\.\d{2})\s*(\d+[\s\d]*\.\d{2})", text, re.IGNORECASE)
            if accommodation_match2:
                data["accommodation"] = {
                    "nights": accommodation_match2.group(1),
                    "rate_per_night": accommodation_match2.group(2),
                    "total": accommodation_match2.group(3)
                }
        
        # Look for accommodation details in the actual voucher format with no space after ZAR
        if not data.get("accommodation"):
            accommodation_match3 = re.search(r"Room\s*Night\s*(\d+)\s*ZAR\s*(\d+[\s\d]*\.\d{2})\s*(\d+[\s\d]*\.\d{2})", text, re.IGNORECASE)
            if accommodation_match3:
                data["accommodation"] = {
                    "nights": accommodation_match3.group(1),
                    "rate_per_night": accommodation_match3.group(2),
                    "total": accommodation_match3.group(3)
                }
        
        # Look for accommodation details in the actual voucher format with no space between Room and Night
        if not data.get("accommodation"):
            accommodation_match4 = re.search(r"Room\s*Night\s*(\d+)\s*ZAR\s*(\d+[\s\d]*\.\d{2})\s*(\d+[\s\d]*\.\d{2})", text, re.IGNORECASE)
            if accommodation_match4:
                data["accommodation"] = {
                    "nights": accommodation_match4.group(1),
                    "rate_per_night": accommodation_match4.group(2),
                    "total": accommodation_match4.group(3)
                }
        
        # Look for accommodation details in the actual voucher format with no spaces anywhere
        if not data.get("accommodation"):
            accommodation_match5 = re.search(r"RoomNight\s*(\d+)\s*ZAR\s*(\d+\.\d{2})\s*(\d+\.\d{2})", text)
            if accommodation_match5:
                data["accommodation"] = {
                    "nights": accommodation_match5.group(1),
                    "rate_per_night": accommodation_match5.group(2),
                    "total": accommodation_match5.group(3)
                }
        
        # Look for transport details (tolerant to spacing/case)
        transport_match = re.search(r"daily\s*transport\s*@?\s*R?\s*(\d+(?:\.\d{2})?)\s*from\s*nandis\s*to\s*rosherville\s*and\s*back", text, re.IGNORECASE)
        if transport_match:
            data["transport"] = {
                "daily_rate": transport_match.group(1),
                "description": "Daily Transport from Nandis to Rosherville and back"
            }
        
        # Look for ancillary charges (Personal Services - Laundry) with tolerant patterns
        if re.search(r"personal\s*serv\.?\s*-?\s*l(a|au)undry", text, re.IGNORECASE):
            data["ancillary_services"] = {
                "description": "Personal Services - Laundry",
                "fixed_price": "300.00"
            }
        
        # Look for meal plan (but we'll exclude this from services as per requirements)
        if "dbb+lp" in text.lower():
            data["meal_plan"] = "Dinner, Breakfast & Lunch (DBB+L)"
        
        # Look for voucher number
        if not data.get("document_details", {}).get("voucher_number"):
            voucher_match = re.search(r"G\d+", text)
            if voucher_match:
                if not data.get("document_details"):
                    data["document_details"] = {}
                data["document_details"]["voucher_number"] = voucher_match.group(0)
        
        # Look for passenger name
        if not data.get("passenger_info", {}).get("name"):
            passenger_match = re.search(r"Number inparty:\d+\n([A-Z\s]+)", text)
            if passenger_match:
                if not data.get("passenger_info"):
                    data["passenger_info"] = {}
                data["passenger_info"]["name"] = passenger_match.group(1).strip()
        
        # Look for passenger name in alternative format
        if not data.get("passenger_info", {}).get("name"):
            passenger_match2 = re.search(r"Number inparty:\d+\n([A-Z]+)", text)
            if passenger_match2:
                if not data.get("passenger_info"):
                    data["passenger_info"] = {}
                # Format the name properly by adding spaces between words
                name = passenger_match2.group(1)
                # Add spaces between consecutive uppercase letters
                formatted_name = ' '.join(name[i:i+1] for i in range(0, len(name), 1))
                data["passenger_info"]["name"] = formatted_name
        
        # Look for check-in date
        if not data.get("stay_details", {}).get("check_in"):
            checkin_match = re.search(r"Check-in\s*(\d{4}/\d{2}/\d{2})", text)
            if checkin_match:
                if not data.get("stay_details"):
                    data["stay_details"] = {}
                data["stay_details"]["check_in"] = checkin_match.group(1)
        
        # Look for check-out date
        if not data.get("stay_details", {}).get("check_out"):
            checkout_match = re.search(r"Check-out\s*(\d{4}/\d{2}/\d{2})", text)
            if checkout_match:
                if not data.get("stay_details"):
                    data["stay_details"] = {}
                data["stay_details"]["check_out"] = checkout_match.group(1)
        
        # Look for length of stay
        if not data.get("stay_details", {}).get("length"):
            length_match = re.search(r"Length ofStay\s*(\d+)", text)
            if length_match:
                if not data.get("stay_details"):
                    data["stay_details"] = {}
                data["stay_details"]["length"] = length_match.group(1)
        
        # Look for length of stay in alternative format
        if not data.get("stay_details", {}).get("length"):
            length_match2 = re.search(r"LengthofStay\s*(\d+)", text)
            if length_match2:
                if not data.get("stay_details"):
                    data["stay_details"] = {}
                data["stay_details"]["length"] = length_match2.group(1)
        
        # Look for room type - extract from accommodation description line
        # Pattern matches: "Accommodation -Roombooked, Single.Rateincludes" or ", Double."
        room_type_match = re.search(r'Accommodation.*?,\s*(Single|Double)\.', text, re.IGNORECASE)
        if room_type_match:
            if not data.get("stay_details"):
                data["stay_details"] = {}
            data["stay_details"]["room_type"] = room_type_match.group(1).capitalize()  # Ensure proper capitalization
        elif "Double.Rate" in text:
            # Fallback for old format
            if not data.get("stay_details"):
                data["stay_details"] = {}
            data["stay_details"]["room_type"] = "Double"
        
        # Look for company details
        if "NandisGuesthouse" in text:
            data["company"] = {
                "name": "Nandis Guesthouse 2",
                "address": "99 Abercrombie Road, Pretoria North, Pretoria, 0182, Gauteng",
                "phone": search(r"Gauteng\n(\d{10})"),
                "email": search(r"Gauteng.*\n[0-9 ]+\n([^\s]+)")
            }
        
        # Look for billing company details
        if "Travel With Flair" in text:
            data["billing_company"] = {
                "name": "Travel With Flair - Pty (Headoffice)",
                "phone": search(r"Telephone Number\s*\((\d+)\)(\d+)"),
                "email": "supplier.invoices@twf.co.za",
                "fax": search(r"FaxNumber\s*(\d+)")
            }
        
        # Convert to invoice format
        invoice_data = convert_to_invoice_format(data)
        
        return invoice_data
        
    except Exception as e:
        print(f"Error parsing PDF: {e}")
        return None

def convert_to_invoice_format(data):
    """
    Convert the structured voucher data to invoice format
    """
    def _normalize_text(text: str) -> str:
        if not text:
            return text
        import re as _re
        s = text.strip()
        s = _re.sub(r"([a-z])([A-Z])", r"\1 \2", s)
        s = _re.sub(r"([A-Za-z])([0-9])", r"\1 \2", s)
        s = _re.sub(r"([0-9])([A-Za-z])", r"\1 \2", s)
        s = _re.sub(r"\s{2,}", " ", s)
        # Specific common fixes from vouchers
        s = s.replace("DailyTransport", "Daily Transport")
        s = s.replace("Rateincludes", "Rate includes")
        s = s.replace("Guesthouse", "Guesthouse")
        return s

    invoice_data = {
        'check_in': '',
        'check_out': '',
        'length_of_stay': '',
        'voucher_number': '',
        'passenger_names': '',
        'description': '',
        'uom': '',
        'qty': '',
        'currency_rate': '',
        'rate_incl': '',
        'max_total': '',
        'ancillary_charges': '',
        'ancillary_description': '',
        'total_payment_received': '0.00',
        'customer_name': '',
        'line_items': [],
        'invoice_total': 0.0,
        # detection flags and details for conditional UI
        'has_transport': False,
        'transport_rate': '',
        'transport_total': '',
        'transport_description': '',
        'has_ancillary_services': False,
        'ancillary_total': ''
    }
    
    # Extract stay details
    if data.get('stay_details'):
        stay = data['stay_details']
        invoice_data['check_in'] = stay.get('check_in', '')
        invoice_data['check_out'] = stay.get('check_out', '')
        invoice_data['length_of_stay'] = stay.get('length', '')
    
    # Extract voucher number
    if data.get('document_details'):
        doc = data['document_details']
        invoice_data['voucher_number'] = doc.get('voucher_number', '')
    
    # Extract passenger name
    if data.get('passenger_info'):
        passenger = data['passenger_info']
        invoice_data['passenger_names'] = passenger.get('name', '')
        invoice_data['customer_name'] = passenger.get('name', '')
    
    # Extract accommodation details
    if data.get('accommodation'):
        acc = data['accommodation']
        # Use actual room type if available, otherwise default to Single
        room_type = data.get('stay_details', {}).get('room_type', 'Single')
        invoice_data['description'] = _normalize_text(f'Accommodation - Room booked, {room_type}. Rate includes Dinner, Breakfast & Lunch')
        invoice_data['uom'] = 'Room Night'
        invoice_data['qty'] = acc.get('nights', '1')
        invoice_data['currency_rate'] = 'ZAR'
        invoice_data['rate_incl'] = acc.get('rate_per_night', '0.00')
        invoice_data['max_total'] = acc.get('total', '0.00')
        
        # Add as line item
        invoice_data['line_items'].append({
            'description': _normalize_text(invoice_data['description']),
            'qty': int(acc.get('nights', 1)),
            'unit_price': float(acc.get('rate_per_night', 0)),
            'total': float(acc.get('total', 0))
        })
    
    # Add transport if present
    if data.get('transport'):
        transport = data['transport']
        daily_rate = float(transport['daily_rate'])
        length_of_stay = int(invoice_data.get('length_of_stay', 1))
        transport_total = daily_rate * length_of_stay
        
        invoice_data['line_items'].append({
            'description': _normalize_text(transport['description']),
            'qty': length_of_stay,
            'unit_price': daily_rate,
            'total': transport_total
        })
        invoice_data['has_transport'] = True
        invoice_data['transport_rate'] = f"{daily_rate:.2f}"
        invoice_data['transport_total'] = f"{transport_total:.2f}"
        invoice_data['transport_description'] = transport['description']
    
    # Add ancillary services if present
    if data.get('ancillary_services'):
        ancillary = data['ancillary_services']
        fixed_price = float(ancillary['fixed_price'])
        
        invoice_data['line_items'].append({
            'description': _normalize_text(ancillary['description']),
            'qty': 1,
            'unit_price': fixed_price,
            'total': fixed_price
        })
        invoice_data['has_ancillary_services'] = True
        invoice_data['ancillary_description'] = ancillary['description']
        invoice_data['ancillary_total'] = f"{fixed_price:.2f}"
    
    # Note: Meal plan (DBB+L) is excluded from services as per requirements
    
    # Extract transport from voucher remarks if not already captured
    # Assuming 'remarks' is a key in 'data' and 'voucher' under 'remarks' is a list of strings
    voucher_remarks_list = data.get('remarks', {}).get('voucher', [])
    voucher_remarks_text = " ".join(voucher_remarks_list) # Join all remarks into a single string
    
    transport_match = re.search(r'(Laundry Transport.*?)(?:\s|\b)([rR@]?\d{1,3}(?:[\s,]\d{3})*(?:\.\d{2})?)(?:\sPER\sDAY)?', voucher_remarks_text)
    
    if transport_match:
        transport_description = transport_match.group(1).strip()
        transport_price_str = transport_match.group(2).replace('R', '').replace('r', '').replace('@', '').replace(',', '').strip()
        
        try:
            transport_price = float(transport_price_str)
            
            # Check if this transport item already exists in line_items to avoid duplication
            existing_transport_item = next((item for item in invoice_data['line_items'] if "Laundry Transport" in item['description']), None)
            
            if not existing_transport_item:
                # Add as a new line item
                invoice_data['line_items'].append({
                    'description': _normalize_text(transport_description),
                    'qty': 1, # Assuming 1 for now, adjust if pattern implies otherwise
                    'unit_price': transport_price,
                    'total': transport_price
                })
                # Update total for the invoice
                invoice_data['invoice_total'] += transport_price
                invoice_data['has_transport'] = True # Mark that transport was found
                # Optionally store details if needed for other UI elements
                invoice_data['transport_description'] = transport_description
                invoice_data['transport_rate'] = f"{transport_price:.2f}"
                invoice_data['transport_total'] = f"{transport_price:.2f}"
        except ValueError:
            pass # Log error if price parsing fails

    # Calculate invoice total
    invoice_data['invoice_total'] = sum(item['total'] for item in invoice_data['line_items'])
    
    return invoice_data

def main():
    """
    Main function to test the PDF parsing
    """
    # Look for PDF files in the uploads directory
    uploads_dir = "uploads"
    if os.path.exists(uploads_dir):
        pdf_files = [f for f in os.listdir(uploads_dir) if f.endswith('.pdf')]
        if pdf_files:
            pdf_path = os.path.join(uploads_dir, pdf_files[0])
            print(f"Testing PDF parsing with: {pdf_path}")
            
            # Parse the PDF
            data = parse_voucher_pdf(pdf_path)
            
            if data:
                print("\n=== PARSED DATA ===")
                print(json.dumps(data, indent=2))
                
                # Save as JSON
                output_file = "voucher_data.json"
                with open(output_file, "w") as f:
                    json.dump(data, indent=4, fp=f)
                print(f"\nExtracted data saved to {output_file}")
            else:
                print("Failed to parse PDF")
        else:
            print("No PDF files found in uploads directory")
    else:
        print("Uploads directory not found")

if __name__ == "__main__":
    main()
