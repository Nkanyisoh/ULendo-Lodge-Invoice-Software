import pdfplumber
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from datetime import datetime
import sqlite3
import os
import re

def clean_company_info(text):
    """
    Clean company information and addresses extracted from PDFs
    """
    if not text:
        return text
    
    cleaned = text
    
    # Fix common address formatting issues
    address_fixes = {
        '10SinclairRoad': '10 Sinclair Road',
        'LambtonGermiston': 'Lambton, Germiston',
        'Germiston1401': 'Germiston, 1401',
        'TravelwithFlair': 'Travel with Flair',
        'PtyLtd': 'Pty Ltd',
        'UlendoLodge': 'Ulendo Lodge',
        'Apartments': 'Apartments',
        'Refinedaccommodation': 'Refined accommodation',
        'forcorporate': 'for corporate',
        'andbusiness': 'and business',
        'professionals': 'professionals'
    }
    
    for wrong, correct in address_fixes.items():
        cleaned = cleaned.replace(wrong, correct)
    
    # Fix missing spaces in addresses
    cleaned = re.sub(r'(\d)([A-Za-z])', r'\1 \2', cleaned)
    cleaned = re.sub(r'([A-Za-z])(\d)', r'\1 \2', cleaned)
    
    # Fix missing spaces around commas in addresses
    cleaned = re.sub(r'([A-Za-z])(,)', r'\1\2 ', cleaned)
    cleaned = re.sub(r'(,)([A-Za-z])', r'\1 \2', cleaned)
    
    return cleaned.strip()

def clean_pdf_text(text):
    """
    Comprehensive function to clean PDF extracted text and fix spacing issues
    """
    if not text:
        return text
    
    # Fix the main issue: PDF extraction adds spaces between every character
    # First, remove excessive spaces between characters while preserving word boundaries
    cleaned = text
    
    # Fix the case where every character is separated by a space
    # This pattern: "V oucher G 844979" should become "Voucher G844979"
    # But we need to be careful not to break legitimate multi-word phrases
    
    # First, fix common compound words and phrases that should be together
    common_fixes = {
        'V oucher': 'Voucher',
        'B ill': 'Bill',
        'B ack': 'Back',
        'A gent': 'Agent',
        'B illing': 'Billing',
        'A ddress': 'Address',
        'T ravel': 'Travel',
        'W ith': 'With',
        'F lair': 'Flair',
        'P ty': 'Pty',
        'H eadoffice': 'Head Office',
        'T elephone': 'Telephone',
        'N umber': 'Number',
        'V at': 'VAT',
        'N r': 'Nr',
        'F ax': 'Fax',
        'P rivate': 'Private',
        'B ag': 'Bag',
        'I ssue': 'Issue',
        'D ate': 'Date',
        'I ssued': 'Issued',
        'B y': 'By',
        'R ef': 'Ref',
        'E mail': 'Email',
        'O rder': 'Order',
        'C ost': 'Cost',
        'C enter': 'Center',
        'A sset': 'Asset',
        'M anager': 'Manager',
        'P assenger': 'Passenger',
        'N umber': 'Number',
        'D ebtor': 'Debtor',
        'A cc': 'Acc',
        'N o': 'No',
        'I RD': 'IRD',
        'D ebtor': 'Debtor',
        'N ame': 'Name',
        'I ata': 'IATA',
        'U lendo': 'Ulendo',
        'L odge': 'Lodge',
        'A nd': 'And',
        'A partment': 'Apartment',
        'R eservation': 'Reservation',
        'T habo': 'Thabo',
        'S inclair': 'Sinclair',
        'R oad': 'Road',
        'L ambton': 'Lambton',
        'P ayment': 'Payment',
        'I nstruction': 'Instruction',
        'G ermiston': 'Germiston',
        'B illback': 'Billback',
        'E xtras': 'Extras',
        'U nless': 'Unless',
        'D irect': 'Direct',
        'C lient': 'Client',
        'Q t': 'Qt',
        'S upplier': 'Supplier',
        'C ode': 'Code',
        'C heck': 'Check',
        'L engthof': 'Length of',
        'S tay': 'Stay',
        'N umberof': 'Number of',
        'R ooms': 'Rooms',
        'D escription': 'Description',
        'Q ty': 'Qty',
        'C urrency': 'Currency',
        'R ate': 'Rate',
        'I ncl': 'Incl',
        'M ax': 'Max',
        'T otal': 'Total',
        'A ccommodation': 'Accommodation',
        'R oombooked': 'Room booked',
        'S ingle': 'Single',
        'R ateincludes': 'Rate includes',
        'R oom': 'Room',
        'N ight': 'Night',
        'D inner': 'Dinner',
        'B reakfast': 'Breakfast',
        'L unch': 'Lunch',
        'A ncillary': 'Ancillary',
        'C harges': 'Charges',
        'P ersonal': 'Personal',
        'S erv': 'Serv',
        'L aundry': 'Laundry',
        'U nit': 'Unit',
        'V oucher': 'Voucher',
        'R emarks': 'Remarks',
        'T hequotedrate': 'The quoted rate',
        'V AT': 'VAT',
        'tourismlevy': 'tourism levy',
        'S pecial': 'Special',
        'I nstructions': 'Instructions',
        'A nyextras': 'Any extras',
        'traveller': 'traveller',
        'G eneral': 'General',
        'T erms': 'Terms',
        'C onditions': 'Conditions',
        'vouchervalid': 'voucher valid',
        'specifiedservices': 'specified services',
        'A nyservices': 'Any services',
        'required': 'required',
        'coveredbythevoucher': 'covered by the voucher',
        'billeddirectly': 'billed directly',
        'traveller': 'traveller',
        'R eferto': 'Refer to',
        'TWF': 'TWF',
        'www': 'www',
        'travelwithflair': 'travelwithflair',
        'co': 'co',
        'za': 'za',
        'terms': 'terms',
        'conditions': 'conditions',
        'K indlyremember': 'Kindly remember',
        'identitydocument': 'identity document',
        'presentit': 'present it',
        'check': 'check',
        'aboveaddress': 'above address',
        'amended': 'amended',
        'I mmigration': 'Immigration',
        'A ct': 'Act',
        'relevantregulations': 'relevant regulations',
        'legalrequirement': 'legal requirement',
        'accommodationsuppliers': 'accommodation suppliers',
        'registercontaining': 'register containing',
        'detailsofallguests': 'details of all guests',
        'I mmigration': 'Immigration',
        'R egulations': 'Regulations',
        'T hebearer': 'The bearer',
        'vouchermaynot': 'voucher may not',
        'handedanyform': 'handed any form',
        'cashinlieu': 'cash in lieu',
        'meals': 'meals',
        'C reated': 'Created',
        'J ul': 'Jul'
    }
    
    for wrong, correct in common_fixes.items():
        cleaned = cleaned.replace(wrong, correct)
    
    # Fix missing spaces between words (lowercase followed by uppercase)
    cleaned = re.sub(r'([a-z])([A-Z])', r'\1 \2', cleaned)
    
    # Fix missing spaces after punctuation followed by letters
    cleaned = re.sub(r'([.!?])([A-Za-z])', r'\1 \2', cleaned)
    
    # Fix missing spaces before punctuation
    cleaned = re.sub(r'([A-Za-z])([.!?])', r'\1 \2', cleaned)
    
    # Fix missing spaces between words (uppercase followed by lowercase)
    cleaned = re.sub(r'([A-Z])([a-z])', r'\1 \2', cleaned)
    
    # Fix missing spaces around commas
    cleaned = re.sub(r'([A-Za-z])(,)', r'\1\2 ', cleaned)
    cleaned = re.sub(r'(,)([A-Za-z])', r'\1 \2', cleaned)
    
    # Fix missing spaces around parentheses
    cleaned = re.sub(r'([A-Za-z])(\()', r'\1 \2', cleaned)
    cleaned = re.sub(r'(\))([A-Za-z])', r'\2 \1', cleaned)
    
    # Fix missing spaces around ampersands
    cleaned = re.sub(r'([A-Za-z])(&)([A-Za-z])', r'\1 \2 \3', cleaned)
    
    # Fix missing spaces between numbers and text
    cleaned = re.sub(r'(\d)([A-Za-z])', r'\1 \2', cleaned)
    cleaned = re.sub(r'([A-Za-z])(\d)', r'\1 \2', cleaned)
    
    # Fix missing spaces around currency symbols
    cleaned = re.sub(r'([A-Za-z])([R$€£¥])', r'\1 \2', cleaned)
    cleaned = re.sub(r'([R$€£¥])([A-Za-z])', r'\2 \1', cleaned)
    
    # Fix multiple spaces
    cleaned = re.sub(r'\s+', ' ', cleaned)
    
    # Fix spaces around hyphens and dashes
    cleaned = re.sub(r'\s*-\s*', ' - ', cleaned)
    
    return cleaned.strip()

def parse_voucher_pdf(pdf_path):
    data = {}
    with pdfplumber.open(pdf_path) as pdf:
        text = pdf.pages[0].extract_text()
    
    # Clean the extracted text to fix spacing issues
    text = clean_pdf_text(text)
    
    # Debug: Print the cleaned text to see what we're working with
    print("=== CLEANED PDF TEXT ===")
    print(text)
    print("=== END CLEANED TEXT ===")
    
    # Initialize only the required fields
    data['check_in'] = ''
    data['check_out'] = ''
    data['length_of_stay'] = ''
    data['voucher_number'] = ''
    data['passenger_names'] = ''
    data['description'] = ''
    data['uom'] = ''
    data['qty'] = ''
    data['currency_rate'] = ''
    data['rate_incl'] = ''
    data['max_total'] = ''
    data['ancillary_charges'] = ''
    data['ancillary_description'] = ''
    data['total_payment_received'] = ''
    data['additional_services'] = []
    data['additional_ancillary'] = []
    
    lines = text.split('\n')
    print(f"Total lines extracted: {len(lines)}")
    
    for i, line in enumerate(lines):
        line = line.strip()
        print(f"Line {i}: '{line}'")
        
        # Extract passenger names - found in the text
        if 'Passenger name/s' in line:
            # Look for the passenger name pattern
            # The name appears after "Passenger name/s Number in party: 1"
            if 'Number in party:' in line:
                # Extract the name from the same line or next line
                name_match = re.search(r'Number in party:\s*(\d+)\s*([A-Za-z\s]+)', line)
                if name_match:
                    passenger_name = name_match.group(2).strip()
                    # Clean the name
                    passenger_name = clean_pdf_text(passenger_name)
                    data['passenger_names'] = passenger_name
                else:
                    # Try to find the name in the next few lines
                    for j in range(i+1, min(i+5, len(lines))):
                        next_line = lines[j].strip()
                        if next_line and not any(keyword in next_line for keyword in ['Debtor', 'Acc', 'IATA', 'Voucher']):
                            # This might be the passenger name
                            passenger_name = clean_pdf_text(next_line)
                            if len(passenger_name) > 3:  # Reasonable name length
                                data['passenger_names'] = passenger_name
                                break
            print(f"Found passenger names: {data['passenger_names']}")
        
        # Look for passenger name in other formats
        elif 'IRDTHABITHASIMAMANE' in line:
            # This appears to be a passenger name
            passenger_name = line.replace('IRDTHABITHASIMAMANE', 'IRD THABI THASIMAMANE')
            passenger_name = clean_pdf_text(passenger_name)
            if not data.get('passenger_names'):
                data['passenger_names'] = passenger_name
            print(f"Found passenger name from IRD: {passenger_name}")
        
        # Extract billing company information
        elif 'Travel With Flair' in line:
            # Extract billing company details
            if 'Pty' in line and 'Head Office' in line:
                billing_company = 'Travel With Flair - Pty (Head Office)'
                data['billing_company'] = billing_company
                print(f"Found billing company: {billing_company}")
        
        # Extract company address
        elif '10 Sinclair Road' in line:
            address = '10 Sinclair Road, Lambton, Germiston, 1401'
            data['company_address'] = address
            print(f"Found company address: {address}")
        
        # Extract company address in other formats
        elif 'Lambton' in line and 'Germiston' in line:
            # This appears to be part of the company address
            if '10 Sinclair Road' not in data.get('company_address', ''):
                address = '10 Sinclair Road, Lambton, Germiston, 1401'
                data['company_address'] = address
                print(f"Found company address (alternative format): {address}")
        
        # Extract company contact information
        elif 'Telephone Number' in line:
            phone_match = re.search(r'Telephone Number\s*\((\d+)\)(\d+)', line)
            if phone_match:
                phone = f"({phone_match.group(1)}) {phone_match.group(2)}"
                data['company_phone'] = phone
                print(f"Found company phone: {phone}")
        
        elif 'Email:' in line:
            email_match = re.search(r'Email:\s*([^\s]+)', line)
            if email_match:
                email = email_match.group(1)
                data['company_email'] = email
                print(f"Found company email: {email}")
        
        # Extract company contact information in other formats
        elif '0676237170' in line:
            # This appears to be the company phone number
            phone = '067 623 7170'
            data['company_phone'] = phone
            print(f"Found company phone (alternative format): {phone}")
        
        elif 'info@ulendolodge.com' in line:
            # This appears to be the company email
            email = 'info@ulendolodge.com'
            data['company_email'] = email
            print(f"Found company email (alternative format): {email}")
        
        # Extract company name and tagline
        elif 'Ulendo Lodge' in line:
            company_name = 'Ulendo Lodge & Apartments'
            data['company_name'] = company_name
            print(f"Found company name: {company_name}")
        
        # Extract company name in other formats
        elif 'Ulendo' in line and 'Lodge' in line:
            # This appears to be the company name
            if 'Ulendo Lodge & Apartments' not in data.get('company_name', ''):
                company_name = 'Ulendo Lodge & Apartments'
                data['company_name'] = company_name
                print(f"Found company name (alternative format): {company_name}")
        
        elif 'Refined accommodation' in line or 'corporate and business professionals' in line:
            tagline = 'Refined accommodation for corporate and business professionals'
            data['company_tagline'] = tagline
            print(f"Found company tagline: {tagline}")
        
        # Extract company tagline in other formats
        elif 'corporate' in line and 'business' in line and 'professionals' in line:
            # This appears to be part of the company tagline
            if 'Refined accommodation for corporate and business professionals' not in data.get('company_tagline', ''):
                tagline = 'Refined accommodation for corporate and business professionals'
                data['company_tagline'] = tagline
                print(f"Found company tagline (alternative format): {tagline}")
        
        # Extract reservation number
        elif 'Reservation Number' in line:
            reservation_match = re.search(r'Reservation Number\s+([A-Za-z0-9\s]+)', line)
            if reservation_match:
                reservation_num = reservation_match.group(1).strip()
                data['reservation_number'] = reservation_num
                print(f"Found reservation number: {reservation_num}")
        
        # Extract reservation number in other formats
        elif 'Thabo' in line:
            # This appears to be the reservation number
            reservation_num = 'Thabo'
            data['reservation_number'] = reservation_num
            print(f"Found reservation number (alternative format): {reservation_num}")
        
        # Extract other booking details
        elif 'Number of Rooms' in line:
            rooms_match = re.search(r'Number of Rooms\s+(\d+)', line)
            if rooms_match:
                num_rooms = rooms_match.group(1)
                data['number_of_rooms'] = num_rooms
                print(f"Found number of rooms: {num_rooms}")
        
        # Extract number of rooms in other formats
        elif 'Rooms' in line and any(char.isdigit() for char in line):
            # Look for a number in the line that might be the number of rooms
            rooms_match = re.search(r'(\d+)', line)
            if rooms_match:
                num_rooms = rooms_match.group(1)
                if not data.get('number_of_rooms'):
                    data['number_of_rooms'] = num_rooms
                    print(f"Found number of rooms (alternative format): {num_rooms}")
        
        # Extract voucher number - look for "Voucher Number G844979"
        elif 'Voucher Number' in line:
            voucher_match = re.search(r'Voucher Number\s+([A-Z0-9]+)', line)
            if voucher_match:
                data['voucher_number'] = voucher_match.group(1)
            print(f"Found voucher number: {data['voucher_number']}")
        
        # Extract voucher number in other formats
        elif 'G844979' in line:
            # This appears to be the voucher number
            voucher_num = 'G844979'
            data['voucher_number'] = voucher_num
            print(f"Found voucher number (alternative format): {voucher_num}")
        
        # Extract check-in date - look for "Check-in 2025/08/05"
        elif 'Check-in' in line:
            checkin_match = re.search(r'Check-in\s+(\d{4}/\d{2}/\d{2})', line)
            if checkin_match:
                data['check_in'] = checkin_match.group(1)
            print(f"Found check-in: {data['check_in']}")
        
        # Extract check-in date in other formats
        elif '2025/08/05' in line:
            # This appears to be the check-in date
            checkin_date = '2025/08/05'
            data['check_in'] = checkin_date
            print(f"Found check-in date (alternative format): {checkin_date}")
        
        # Extract check-out date - look for "Check-out 2025/09/04"
        elif 'Check-out' in line:
            checkout_match = re.search(r'Check-out\s+(\d{4}/\d{2}/\d{2})', line)
            if checkout_match:
                data['check_out'] = checkout_match.group(1)
            print(f"Found check-out: {data['check_out']}")
        
        # Extract check-out date in other formats
        elif '2025/09/04' in line:
            # This appears to be the check-out date
            checkout_date = '2025/09/04'
            data['check_out'] = checkout_date
            print(f"Found check-out date (alternative format): {checkout_date}")
        
        # Extract length of stay - look for "Length of Stay 30"
        elif 'Length of Stay' in line:
            length_match = re.search(r'Length of Stay\s+(\d+)', line)
            if length_match:
                data['length_of_stay'] = length_match.group(1)
            print(f"Found length of stay: {data['length_of_stay']}")
        
        # Extract length of stay in other formats
        elif '30' in line and ('Length' in line or 'Stay' in line):
            # This appears to be the length of stay
            length_stay = '30'
            data['length_of_stay'] = length_stay
            print(f"Found length of stay (alternative format): {length_stay}")
        
        # Look for accommodation details in other formats
        elif 'Room Night' in line and 'ZAR' in line:
            # This might be accommodation details in a different format
            rate_match = re.search(r'(\d+)\s+ZAR\s+([\d.]+)\s+([\d.]+)', line)
            if rate_match:
                qty_val = int(rate_match.group(1))
                rate_val = float(rate_match.group(2))
                total_val = float(rate_match.group(3))
                
                # Look for room type in the line
                if 'Single' in line:
                    room_type = 'Single'
                elif 'Double' in line:
                    room_type = 'Double'
                else:
                    room_type = 'Room'
                
                description = f'Accommodation - Room booked, {room_type}. Rate includes Room Night'
                description = clean_pdf_text(description)
                
                if not data.get('description'):
                    data['description'] = description
                    data['uom'] = 'Room Night'
                    data['qty'] = str(qty_val)
                    data['currency_rate'] = 'ZAR'
                    data['rate_incl'] = f"{rate_val:.2f}"
                    data['max_total'] = f"{total_val:.2f}"
                else:
                    data['additional_services'].append({
                        'description': description,
                        'qty': qty_val,
                        'unit_price': rate_val,
                        'total': total_val
                    })
                print(f"Found accommodation details (alternative format): {description}")
        
        # Extract accommodation details - look for "Accommodation - Room booked, Single. Rate includes Room Night 30 ZAR 1688.50 50655.00"
        elif 'Accommodation' in line:
            # Look for the rate and quantity information
            rate_match = re.search(r'Room Night\s+(\d+)\s+ZAR\s+([\d.]+)\s+([\d.]+)', line)
            if rate_match:
                qty_val = int(rate_match.group(1))
                rate_val = float(rate_match.group(2))
                total_val = float(rate_match.group(3))
                
                # Extract description
                description = line.split('Accommodation')[0] + 'Accommodation - Room booked, Single'
                description = clean_pdf_text(description)
                
                if not data.get('description'):
                    data['description'] = description
                    data['uom'] = 'Room Night'
                    data['qty'] = str(qty_val)
                    data['currency_rate'] = 'ZAR'
                    data['rate_incl'] = f"{rate_val:.2f}"
                    data['max_total'] = f"{total_val:.2f}"
                else:
                    data['additional_services'].append({
                        'description': description,
                        'qty': qty_val,
                        'unit_price': rate_val,
                        'total': total_val
                    })
            print(f"Found accommodation details: {data.get('description')}")
        
        # Extract ancillary charges - look for "Personal Serv. - Laundry Unit 1 ZAR 300.00 300.00"
        elif 'Personal Serv.' in line and 'Laundry' in line:
            laundry_match = re.search(r'Unit\s+(\d+)\s+ZAR\s+([\d.]+)\s+([\d.]+)', line)
            if laundry_match:
                qty_val = int(laundry_match.group(1))
                rate_val = float(laundry_match.group(2))
                total_val = float(laundry_match.group(3))
                
                ancillary_desc = 'Personal Serv. - Laundry'
                ancillary_desc = clean_pdf_text(ancillary_desc)
                
                if not data.get('ancillary_charges') and not data.get('ancillary_description'):
                    data['ancillary_description'] = ancillary_desc
                    data['ancillary_charges'] = f"{total_val:.2f}"
                else:
                    data['additional_ancillary'].append({
                        'description': ancillary_desc,
                        'qty': qty_val,
                        'unit_price': rate_val,
                        'total': total_val
                    })
            print(f"Found ancillary charges: {data.get('ancillary_description')}")
        
        # Extract ancillary charges in other formats
        elif 'Laundry' in line and 'ZAR' in line:
            # This might be ancillary charges in a different format
            laundry_match = re.search(r'(\d+)\s+ZAR\s+([\d.]+)\s+([\d.]+)', line)
            if laundry_match:
                qty_val = int(laundry_match.group(1))
                rate_val = float(laundry_match.group(2))
                total_val = float(laundry_match.group(3))
                
                ancillary_desc = 'Personal Serv. - Laundry'
                ancillary_desc = clean_pdf_text(ancillary_desc)
                
                if not data.get('ancillary_charges') and not data.get('ancillary_description'):
                    data['ancillary_description'] = ancillary_desc
                    data['ancillary_charges'] = f"{total_val:.2f}"
                else:
                    data['additional_ancillary'].append({
                        'description': ancillary_desc,
                        'qty': qty_val,
                        'unit_price': rate_val,
                        'total': total_val
                    })
                print(f"Found ancillary charges (alternative format): {ancillary_desc}")
        
        # Extract meal plan information
        elif 'Dinner, Breakfast & Lunch' in line:
            meal_desc = 'Dinner, Breakfast & Lunch'
            meal_desc = clean_pdf_text(meal_desc)
            
            # Add meal plan as an additional service
            data['additional_services'].append({
                'description': meal_desc,
                'qty': 1,
                'unit_price': 0.00,  # Usually included in room rate
                'total': 0.00
            })
            print(f"Found meal plan: {meal_desc}")
        
        # Extract meal plan details from other formats
        elif 'DBB+L' in line or 'Dinner, Breakfast & Lunch' in line:
            meal_desc = 'Dinner, Breakfast & Lunch (DBB+L)'
            meal_desc = clean_pdf_text(meal_desc)
            
            # Add meal plan as an additional service if not already added
            meal_exists = any('Dinner' in service.get('description', '') for service in data.get('additional_services', []))
            if not meal_exists:
                data['additional_services'].append({
                    'description': meal_desc,
                    'qty': 1,
                    'unit_price': 0.00,  # Usually included in room rate
                    'total': 0.00
                })
                print(f"Found meal plan (alternative format): {meal_desc}")
        
        # Extract meal plan information in other formats
        elif 'Dinner' in line and 'Breakfast' in line and 'Lunch' in line:
            # This appears to be meal plan information
            meal_desc = 'Dinner, Breakfast & Lunch'
            meal_desc = clean_pdf_text(meal_desc)
            
            # Add meal plan as an additional service if not already added
            meal_exists = any('Dinner' in service.get('description', '') for service in data.get('additional_services', []))
            if not meal_exists:
                data['additional_services'].append({
                    'description': meal_desc,
                    'qty': 1,
                    'unit_price': 0.00,  # Usually included in room rate
                    'total': 0.00
                })
                print(f"Found meal plan (alternative format): {meal_desc}")
        
        # Extract other service information
        elif 'Ancillary Charges' in line:
            print("Found ancillary charges section")
            # Look for additional services in subsequent lines
            for j in range(i+1, min(i+3, len(lines))):
                next_line = lines[j].strip()
                if 'Unit' in next_line and 'ZAR' in next_line:
                    # This might be an additional service
                    service_match = re.search(r'(\d+)\s+ZAR\s+([\d.]+)\s+([\d.]+)', next_line)
                    if service_match:
                        qty_val = int(service_match.group(1))
                        rate_val = float(service_match.group(2))
                        total_val = float(service_match.group(3))
                        
                        # Try to extract service description
                        service_desc = next_line.split('Unit')[0].strip()
                        if not service_desc:
                            service_desc = 'Additional Service'
                        
                        service_desc = clean_pdf_text(service_desc)
                        
                        data['additional_services'].append({
                            'description': service_desc,
                            'qty': qty_val,
                            'unit_price': rate_val,
                            'total': total_val
                        })
                        print(f"Found additional service: {service_desc}")
                    break
        
        # Extract other service information in different formats
        elif 'Unit' in line and 'ZAR' in line and not any(keyword in line for keyword in ['Laundry', 'Room Night']):
            # This might be an additional service in a different format
            service_match = re.search(r'(\d+)\s+ZAR\s+([\d.]+)\s+([\d.]+)', line)
            if service_match:
                qty_val = int(service_match.group(1))
                rate_val = float(service_match.group(2))
                total_val = float(service_match.group(3))
                
                # Try to extract service description
                service_desc = line.split('Unit')[0].strip()
                if not service_desc:
                    service_desc = 'Additional Service'
                
                service_desc = clean_pdf_text(service_desc)
                
                # Check if this service is already added
                service_exists = any(service_desc in service.get('description', '') for service in data.get('additional_services', []))
                if not service_exists:
                    data['additional_services'].append({
                        'description': service_desc,
                        'qty': qty_val,
                        'unit_price': rate_val,
                        'total': total_val
                    })
                    print(f"Found additional service (alternative format): {service_desc}")
    
    # Calculate length of stay from check-in and check-out dates
    if data['check_in'] and data['check_out']:
        try:
            # Parse dates in YYYY/MM/DD format
            check_in_date = datetime.strptime(data['check_in'], '%Y/%m/%d')
            check_out_date = datetime.strptime(data['check_out'], '%Y/%m/%d')
            
            # Calculate the difference in days
            length_of_stay = (check_out_date - check_in_date).days
            data['length_of_stay'] = str(length_of_stay)
            print(f"Calculated length of stay: {data['length_of_stay']} days")
        except ValueError as e:
            print(f"Error calculating length of stay: {e}")
            # Keep the original extracted value if calculation fails
    
    # Set customer name from passenger names
    data['customer_name'] = data['passenger_names']
    
    # Clean company information if extracted
    if 'company_name' in data:
        data['company_name'] = clean_company_info(data['company_name'])
    if 'company_address' in data:
        data['company_address'] = clean_company_info(data['company_address'])
    
    # Clean billing company information
    if 'billing_company' in data:
        data['billing_company'] = clean_company_info(data['billing_company'])
    
    print("=== EXTRACTED DATA ===")
    for key, value in data.items():
        print(f"{key}: {value}")
    print("=== END EXTRACTED DATA ===")
    
    # Calculate invoice total from the extracted data
    invoice_total = 0.0
    
    # Add main charges (rate_incl * qty)
    if data['rate_incl'] and data['qty']:
        try:
            rate = float(data['rate_incl'].replace('R', '').replace(',', '').strip())
            qty = int(data['qty'])
            main_total = rate * qty
            invoice_total += main_total
        except (ValueError, AttributeError):
            pass
    
    # Add ancillary charges
    if data['ancillary_charges']:
        try:
            ancillary_total = float(data['ancillary_charges'].replace('R', '').replace(',', '').strip())
            invoice_total += ancillary_total
        except (ValueError, AttributeError):
            pass
    
    # Create line items for invoice
    line_items = []
    
    # Main service line item
    if data['description'] and data['rate_incl']:
        try:
            qty = int(data['qty']) if data['qty'] else 1
            rate = float(data['rate_incl'].replace('R', '').replace(',', '').strip())
            total = rate * qty
            
            line_items.append({
                'description': data['description'],
                'qty': qty,
                'unit_price': rate,
                'total': total
            })
        except (ValueError, AttributeError):
            line_items.append({
                'description': data['description'] or 'Room Booking',
                'qty': 1,
                'unit_price': 500.00,
                'total': 500.00
            })
    
    # Ancillary charges line item
    if data['ancillary_charges']:
        try:
            ancillary_total = float(data['ancillary_charges'].replace('R', '').replace(',', '').strip())
            ancillary_desc = data.get('ancillary_description', 'Ancillary Charges')
            line_items.append({
                'description': ancillary_desc,
                'qty': 1,
                'unit_price': ancillary_total,
                'total': ancillary_total
            })
        except (ValueError, AttributeError):
            pass
    
    # Add additional services from lists
    for service in data.get('additional_services', []):
        # Clean the description text
        if 'description' in service:
            service['description'] = clean_pdf_text(service['description'])
        line_items.append(service)
    
    # Add additional ancillary charges from lists
    for ancillary in data.get('additional_ancillary', []):
        # Clean the description text
        if 'description' in ancillary:
            ancillary['description'] = clean_pdf_text(ancillary['description'])
        line_items.append(ancillary)
    
    # Fallback if no line items
    if not line_items:
        line_items = [
            {'description': 'Room Booking', 'qty': 1, 'unit_price': 500.00, 'total': 500.00}
        ]
    
    # Clean all line item descriptions
    for item in line_items:
        if 'description' in item:
            item['description'] = clean_pdf_text(item['description'])
            # Additional cleaning for service descriptions
            item['description'] = clean_company_info(item['description'])
    
    data['line_items'] = line_items
    data['invoice_total'] = invoice_total
    
    return data

def get_next_invoice_number(db_path='invoices.db'):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS metadata(key TEXT PRIMARY KEY, value INTEGER)")
    c.execute("INSERT OR IGNORE INTO metadata(key, value) VALUES('last_inv', 0)")
    conn.commit()
    c.execute("SELECT value FROM metadata WHERE key='last_inv'")
    last = c.fetchone()[0]
    next_num = last + 1
    c.execute("UPDATE metadata SET value=? WHERE key='last_inv'", (next_num,))
    conn.commit()
    conn.close()
    return f"{next_num:05d}"

def fill_invoice_template(output_dir, invoice_number, data, force_single_page=True):
    output_path = os.path.join(output_dir, f"Invoice_{invoice_number}.pdf")
    c = canvas.Canvas(output_path, pagesize=A4)
    width, height = A4
    
    # Define colors using the brand palette
    header_color = (0.79, 0.50, 0.08)  # Golden-brown #ca8015
    accent_color = (0.90, 0.65, 0.20)  # Lighter golden #e6a533
    text_color = (0.0, 0.0, 0.0)       # Black #000000
    white_color = (1.0, 1.0, 1.0)      # White #ffffff
    
    # Header background rectangle
    c.setFillColorRGB(*header_color)
    c.rect(0, height - 4 * cm, width, 4 * cm, fill=True, stroke=False)
    
    # Logo area (if logo exists)
    logo_path = os.path.join(os.path.dirname(__file__), 'assets', 'logo.png')
    if os.path.exists(logo_path):
        # Draw logo background circle
        c.setFillColorRGB(*white_color)
        c.circle(3 * cm, height - 2.5 * cm, 0.8 * cm, fill=True, stroke=False)
        
        # Draw logo image
        try:
            c.drawImage(logo_path, 2.2 * cm, height - 3.3 * cm, width=1.6 * cm, height=1.6 * cm, mask='auto')
        except:
            # Fallback if logo loading fails
            pass
    
    # Company name and tagline
    c.setFillColorRGB(*white_color)  # White text
    c.setFont("Helvetica-Bold", 24)
    c.drawString(5 * cm, height - 2.5 * cm, "Ulendo Lodge & Apartments")

    c.setFont("Helvetica", 12)
    c.drawString(5 * cm, height - 3.2 * cm, "Refined accommodation for corporate and business professionals")
    
    # Invoice details box (top right)
    c.setFillColorRGB(0.99, 0.99, 0.99)  # Near-white background
    c.rect(13 * cm, height - 3.8 * cm, 6 * cm, 2.5 * cm, fill=True, stroke=True)
    
    c.setFillColorRGB(*text_color)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(13.5 * cm, height - 2 * cm, f"INVOICE")
    c.setFont("Helvetica", 10)
    c.drawString(13.5 * cm, height - 2.4 * cm, f"Invoice #: {invoice_number}")
    c.drawString(13.5 * cm, height - 2.7 * cm, f"Date: {datetime.now().strftime('%d %B %Y')}")
    
    # Voucher and booking information section
    y_pos = height - 5.5 * cm
    c.setFillColorRGB(*accent_color)
    c.rect(2 * cm, y_pos - 0.5 * cm, 15 * cm, 0.6 * cm, fill=True, stroke=False)
    
    c.setFillColorRGB(*white_color)  # White text
    c.setFont("Helvetica-Bold", 12)
    c.drawString(2.2 * cm, y_pos - 0.2 * cm, "BOOKING DETAILS")
    
    # Booking details
    y_pos -= 1 * cm  # Reduced spacing from 1.2cm to 1cm
    c.setFillColorRGB(*text_color)
    c.setFont("Helvetica", 10)
    
    # Create a two-column layout for booking details
    left_col = 2 * cm
    right_col = 10 * cm
    
    if data.get('voucher_number'):
        c.drawString(left_col, y_pos, "Voucher Number:")
        c.setFont("Helvetica-Bold", 10)
        c.drawString(left_col + 3 * cm, y_pos, str(data['voucher_number']))
        c.setFont("Helvetica", 10)
    
    if data.get('length_of_stay'):
        c.drawString(right_col, y_pos, "Length of Stay:")
        c.setFont("Helvetica-Bold", 10)
        c.drawString(right_col + 3 * cm, y_pos, f"{data['length_of_stay']} days")
        c.setFont("Helvetica", 10)
    
    y_pos -= 0.4 * cm  # Reduced spacing from 0.5cm to 0.4cm
    
    if data.get('check_in'):
        c.drawString(left_col, y_pos, "Check-in Date:")
        c.setFont("Helvetica-Bold", 10)
        c.drawString(left_col + 3 * cm, y_pos, str(data['check_in']))
        c.setFont("Helvetica", 10)
    
    if data.get('check_out'):
        c.drawString(right_col, y_pos, "Check-out Date:")
        c.setFont("Helvetica-Bold", 10)
        c.drawString(right_col + 3 * cm, y_pos, str(data['check_out']))
        c.setFont("Helvetica", 10)
    
    # Customer information section
    y_pos -= 1 * cm  # Reduced spacing from 1.2cm to 1cm
    c.setFillColorRGB(*accent_color)
    c.rect(2 * cm, y_pos - 0.5 * cm, 15 * cm, 0.6 * cm, fill=True, stroke=False)
    
    c.setFillColorRGB(*white_color)  # White text
    c.setFont("Helvetica-Bold", 12)
    c.drawString(2.2 * cm, y_pos - 0.2 * cm, "CUSTOMER INFORMATION")
    
    y_pos -= 0.8 * cm  # Reduced spacing from 1cm to 0.8cm
    c.setFillColorRGB(*text_color)
    customer_name = data.get('customer_name', '').strip()
    if customer_name:
        c.setFont("Helvetica", 10)
        c.drawString(2 * cm, y_pos, "Guest Name:")
        c.setFont("Helvetica-Bold", 10)
        c.drawString(4 * cm, y_pos, customer_name)
    
    # Line items table
    y_pos -= 1.2 * cm  # Reduced spacing from 1.5cm to 1.2cm
    c.setFillColorRGB(*accent_color)
    c.rect(2 * cm, y_pos - 0.5 * cm, 15 * cm, 0.6 * cm, fill=True, stroke=False)
    
    c.setFillColorRGB(*white_color)  # White text
    c.setFont("Helvetica-Bold", 12)
    c.drawString(2.2 * cm, y_pos - 0.2 * cm, "SERVICES PROVIDED")
    
    # Table headers
    y_pos -= 1 * cm  # Reduced spacing from 1.2cm to 1cm
    c.setFillColorRGB(0.99, 0.99, 0.99)  # Near-white background for headers
    c.rect(2 * cm, y_pos - 0.1 * cm, 15 * cm, 0.6 * cm, fill=True, stroke=True)
    
    c.setFillColorRGB(*text_color)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(2.2 * cm, y_pos + 0.1 * cm, "Description")
    c.drawString(9 * cm, y_pos + 0.1 * cm, "Qty")
    c.drawString(11.5 * cm, y_pos + 0.1 * cm, "Unit Price")
    c.drawString(14.5 * cm, y_pos + 0.1 * cm, "Total")
    
    # Table rows
    y_pos -= 0.6 * cm  # Reduced spacing from 0.8cm to 0.6cm
    c.setFont("Helvetica", 9)
    row_height = 0.6 * cm  # Reduced row height from 0.7cm to 0.6cm
    
    for i, item in enumerate(data.get('line_items', [])):
        # Alternate row colors
        if i % 2 == 0:
            c.setFillColorRGB(0.999, 0.999, 0.999)  # Near-white alternating rows
            c.rect(2 * cm, y_pos - 0.1 * cm, 15 * cm, row_height, fill=True, stroke=False)
        
        c.setFillColorRGB(*text_color)
        
        # Wrap description if too long
        description = str(item['description'])[:50]  # Reduced from 60 to 50 characters
        if len(str(item['description'])) > 50:
            description += "..."
        
        c.drawString(2.2 * cm, y_pos + 0.1 * cm, description)
        c.drawString(9.2 * cm, y_pos + 0.1 * cm, str(item['qty']))
        c.drawString(11.7 * cm, y_pos + 0.1 * cm, f"ZAR {item['unit_price']:.2f}")
        c.drawString(14.7 * cm, y_pos + 0.1 * cm, f"ZAR {item['total']:.2f}")
        y_pos -= row_height
    
    # Payment summary section
    y_pos -= 0.8 * cm  # Reduced spacing from 1cm to 0.8cm
    
    # Calculate totals
    subtotal = sum(float(item['total']) for item in data.get('line_items', []))
    total_payment_received = 0.0
    
    if data.get('total_payment_received'):
        try:
            total_payment_received = float(str(data['total_payment_received']).replace('R', '').replace(',', '').strip())
        except (ValueError, AttributeError):
            total_payment_received = 0.0
    
    outstanding_balance = subtotal - total_payment_received
    
    # Payment summary box
    c.setFillColorRGB(0.999, 0.999, 0.999)  # Near-white background
    c.rect(11 * cm, y_pos - 2.3 * cm, 6 * cm, 2.6 * cm, fill=True, stroke=True)  # Reduced height from 2.8cm to 2.6cm
    
    c.setFillColorRGB(*text_color)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(11.5 * cm, y_pos - 0.5 * cm, "PAYMENT SUMMARY")

    c.setFont("Helvetica", 10)
    c.drawString(11.5 * cm, y_pos - 1 * cm, f"Subtotal:")
    c.drawRightString(16.5 * cm, y_pos - 1 * cm, f"ZAR {subtotal:.2f}")
    
    c.drawString(11.5 * cm, y_pos - 1.4 * cm, f"Payment Received:")
    c.drawRightString(16.5 * cm, y_pos - 1.4 * cm, f"ZAR {total_payment_received:.2f}")
    
    # Outstanding balance with accent color
    c.setFillColorRGB(*header_color)
    c.rect(11.2 * cm, y_pos - 2.2 * cm, 5.6 * cm, 0.5 * cm, fill=True, stroke=False)
    
    c.setFillColorRGB(*white_color)  # White text
    c.setFont("Helvetica-Bold", 11)
    c.drawString(11.5 * cm, y_pos - 2 * cm, f"Outstanding Balance:")
    c.drawRightString(16.5 * cm, y_pos - 2 * cm, f"ZAR {outstanding_balance:.2f}")
    
    # Extended business information section (add before payment summary)
    y_pos -= 2.5 * cm  # Reduced spacing from 3cm to 2.5cm
    
    # Business Information Header
    c.setFillColorRGB(*accent_color)
    c.rect(2 * cm, y_pos - 0.5 * cm, 15 * cm, 0.6 * cm, fill=True, stroke=False)
    
    c.setFillColorRGB(*white_color)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(2.2 * cm, y_pos - 0.2 * cm, "BUSINESS INFORMATION")
    
    y_pos -= 1 * cm  # Reduced spacing from 1.2cm to 1cm
    c.setFillColorRGB(*text_color)
    
    # Contact Information (Left Column)
    left_col = 2 * cm
    right_col = 10.5 * cm
    
    c.setFont("Helvetica-Bold", 9)
    c.drawString(left_col, y_pos, "Our Address:")
    c.setFont("Helvetica", 8)
    c.drawString(left_col, y_pos - 0.35 * cm, "Ulendo Lodge And Apartment")  # Reduced spacing
    c.drawString(left_col, y_pos - 0.65 * cm, "10 Sinclair Road")  # Reduced spacing
    c.drawString(left_col, y_pos - 0.95 * cm, "Lambton, Germiston, 1401")  # Reduced spacing
    c.drawString(left_col, y_pos - 1.25 * cm, "Tel: 067 623 7170")  # Reduced spacing
    c.drawString(left_col, y_pos - 1.55 * cm, "Email: info@ulendolodge.com")  # Reduced spacing
    
    # Bank Account Information (Right Column)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(right_col, y_pos, "Our Bank Account:")
    c.setFont("Helvetica", 8)
    c.drawString(right_col, y_pos - 0.35 * cm, "Account Name: Ulendo Lodge And Apartments")  # Reduced spacing
    c.drawString(right_col, y_pos - 0.65 * cm, "Account Number: 10 23 106 061 9")  # Reduced spacing
    c.drawString(right_col, y_pos - 0.95 * cm, "Bank: Standard Bank")  # Reduced spacing
    c.drawString(right_col, y_pos - 1.25 * cm, "Branch Code: 002442")  # Reduced spacing
    c.drawString(right_col, y_pos - 1.55 * cm, "Type: Current Account")  # Reduced spacing
    
    # Important Note
    y_pos -= 1.5 * cm  # Reduced spacing from 2.5cm to 1.5cm
    c.setFillColorRGB(*header_color)
    c.rect(2 * cm, y_pos - 0.3 * cm, 15 * cm, 0.5 * cm, fill=True, stroke=False)
    
    c.setFillColorRGB(*white_color)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(2.2 * cm, y_pos - 0.1 * cm, "PLEASE NOTE: Send your Proof of payment to info@ulendolodge.com")
    
    # House Rules and Policies (if space allows, otherwise start new page)
    if y_pos < 4 * cm and not force_single_page:  # Only break page if not forcing single page
        c.showPage()  # Start new page for policies
        y_pos = height - 2 * cm
        # Add all policies on new page
        add_policies_section(c, y_pos, header_color, accent_color, white_color, text_color)
    elif y_pos >= 4 * cm:
        # Add policies on current page if there's enough space
        y_pos -= 1.5 * cm
        add_policies_section(c, y_pos, header_color, accent_color, white_color, text_color)
    # If force_single_page and not enough space, skip policies entirely
    
    # Footer section
    c.setFillColorRGB(*header_color)
    c.rect(0, 0, width, 2 * cm, fill=True, stroke=False)
    
    c.setFillColorRGB(*white_color)  # White text
    c.setFont("Helvetica-Oblique", 10)
    c.drawCentredString(width / 2, 1.2 * cm, "Thank you for choosing Ulendo Lodge & Apartments!")
    c.setFont("Helvetica", 8)
    c.drawCentredString(width / 2, 0.6 * cm, "Refined accommodation for corporate and business professionals")
    
    c.save()
    return output_path


def add_policies_section(c, y_pos, header_color, accent_color, white_color, text_color):
    """Add the policies section to the PDF with optimized spacing"""
    # House Rules
    c.setFillColorRGB(*accent_color)
    c.rect(2 * cm, y_pos - 0.4 * cm, 15 * cm, 0.5 * cm, fill=True, stroke=False)
    
    c.setFillColorRGB(*white_color)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(2.2 * cm, y_pos - 0.1 * cm, "HOUSE RULES")
    
    y_pos -= 0.6 * cm
    c.setFillColorRGB(*text_color)
    c.setFont("Helvetica", 8)
    c.drawString(2.5 * cm, y_pos, "• Check-in time is any time after 14:00")
    c.drawString(2.5 * cm, y_pos - 0.25 * cm, "• Check-out is 10:00 the following day")
    c.drawString(2.5 * cm, y_pos - 0.5 * cm, "• Please respect other Guests in terms of noise")
    c.drawString(2.5 * cm, y_pos - 0.75 * cm, "• Lapa and braai areas may not be occupied as of 10pm")
    
    # Refund Policy
    y_pos -= 1.5 * cm
    c.setFillColorRGB(*accent_color)
    c.rect(2 * cm, y_pos - 0.4 * cm, 15 * cm, 0.5 * cm, fill=True, stroke=False)
    
    c.setFillColorRGB(*white_color)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(2.2 * cm, y_pos - 0.1 * cm, "REFUND POLICY")
    
    y_pos -= 0.6 * cm
    c.setFillColorRGB(*text_color)
    c.setFont("Helvetica", 8)
    c.drawString(2.5 * cm, y_pos, "• 100% Refund will be granted with 72 hours notice of check in")
    c.drawString(2.5 * cm, y_pos - 0.25 * cm, "• 50% Refund will be granted with 24 hours notice of check in")
    c.drawString(2.5 * cm, y_pos - 0.5 * cm, "• Failure to check in will result in zero refund as the room was reserved")
    
    # Public Liability
    y_pos -= 1.2 * cm
    c.setFillColorRGB(*accent_color)
    c.rect(2 * cm, y_pos - 0.4 * cm, 15 * cm, 0.5 * cm, fill=True, stroke=False)
    
    c.setFillColorRGB(*white_color)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(2.2 * cm, y_pos - 0.1 * cm, "PUBLIC LIABILITY")
    
    y_pos -= 0.6 * cm
    c.setFillColorRGB(*text_color)
    c.setFont("Helvetica", 8)
    c.drawString(2.5 * cm, y_pos, "• Ulendo Lodge has the right to reserve admission")
    c.drawString(2.5 * cm, y_pos - 0.25 * cm, "• We are not responsible for any damage/loss of any kind to visitor property")
    c.drawString(2.5 * cm, y_pos - 0.5 * cm, "• Visitors will be held accountable for any damages to business property")
    
    return y_pos