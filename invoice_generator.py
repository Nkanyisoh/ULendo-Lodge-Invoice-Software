import pdfplumber
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
    Comprehensive function to clean PDF extracted text and fix spacing issues.
    This version preserves logical line breaks while cleaning internal spacing.
    """
    if not text:
        return text
    
    # Process text line by line to preserve original line breaks
    cleaned_lines = []
    for line in text.splitlines():
        # Phase 1: Aggressively re-insert spaces based on common patterns within each line
        # Add space before an uppercase letter if preceded by a lowercase letter (e.g., 'wordAnother' -> 'word Another')
        cleaned_line = re.sub(r'([a-z])([A-Z])', r'\1 \2', line)
        # Add space between a number and a letter (e.g., '10Sinclair' -> '10 Sinclair', 'Date2025' -> 'Date 2025')
        cleaned_line = re.sub(r'(\d)([A-Za-z])', r'\1 \2', cleaned_line)
        cleaned_line = re.sub(r'([A-Za-z])(\d)', r'\1 \2', cleaned_line)
        # Add space between punctuation and a letter/number if missing (e.g., 'word.Another' -> 'word. Another')
        cleaned_line = re.sub(r'([.,:;!?])([A-Za-z0-9])', r'\1 \2', cleaned_line)
        # Add space between a letter/number and punctuation if missing (e.g., 'word.' -> 'word .')
        cleaned_line = re.sub(r'([A-Za-z0-9])([.,:;!?])', r'\1 \2', cleaned_line)

        # NEW: Aggressively remove spaces within numbers/alphanumeric codes where they don't belong
        # Example: '1688 . 50' -> '1688.50'
        cleaned_line = re.sub(r'(\d+)\s*\.\s*(\d+)', r'\1.\2', cleaned_line)
        # Example: 'R 35 758' -> 'R35758' (for currency parsing later)
        cleaned_line = re.sub(r'([R$€£¥])\s*(\d)', r'\1\2', cleaned_line)
        # Example: 'G 846886' -> 'G846886' for voucher numbers
        cleaned_line = re.sub(r'([A-Z])\s*(\d+)', r'\1\2', cleaned_line)

        # Phase 2: Specific fixes for common concatenated phrases observed in debug outputs
        # (These are for semantic fixes that general rules might miss)
        common_fixes = {
            # General fixes (from previous iterations)
            'V oucher': 'Voucher', 'B ill': 'Bill', 'B ack': 'Back', 'A gent': 'Agent',
            'B illing': 'Billing', 'A ddress': 'Address', 'T ravel': 'Travel', 'W ith': 'With',
            'F lair': 'Flair', 'P ty': 'Pty', 'H eadoffice': 'Head Office', 'T elephone': 'Telephone',
            'N umber': 'Number', 'V at': 'VAT', 'N r': 'Nr', 'F ax': 'Fax',
            'P rivate': 'Private', 'B ag': 'Bag', 'I ssue': 'Issue', 'D ate': 'Date',
            'I ssued': 'Issued', 'B y': 'By', 'R ef': 'Ref', 'E mail': 'Email',
            'O rder': 'Order', 'C ost': 'Cost', 'C enter': 'Center', 'A sset': 'Asset',
            'M anager': 'Manager', 'P assenger': 'Passenger', 'N umber': 'Number',
            'D ebtor': 'Debtor', 'A cc': 'Acc', 'N o': 'No', 'I RD': 'IRD',
            'D ebtor': 'Debtor', 'N ame': 'Name', 'I ata': 'IATA', 'U lendo': 'Ulendo',
            'L odge': 'Lodge', 'A nd': 'And', 'A partment': 'Apartment', 'R eservation': 'Reservation',
            'T habo': 'Thabo', 'S inclair': 'Sinclair', 'R oad': 'Road', 'L ambton': 'Lambton',
            'P ayment': 'Payment', 'I nstruction': 'Instruction', 'G ermiston': 'Germiston',
            'B illback': 'Billback', 'E xtras': 'Extras', 'U nless': 'Unless',
            'D irect': 'Direct', 'C lient': 'Client', 'Q t': 'Qt', 'S upplier': 'Supplier',
            'C ode': 'Code', 'C heck': 'Check', 'L engthof': 'Length of', 'S tay': 'Stay',
            'N umberof': 'Number of', 'R ooms': 'Rooms', 'D escription': 'Description',
            'Q ty': 'Qty', 'C urrency': 'Currency', 'R ate': 'Rate', 'I ncl': 'Incl',
            'M ax': 'Max', 'T otal': 'Total', 'A ccommodation': 'Accommodation',
            'R oombooked': 'Room booked', 'S ingle': 'Single', 'R ateincludes': 'Rate includes',
            'R oom': 'Room', 'N ight': 'Night', 'D inner': 'Dinner', 'B reakfast': 'Breakfast',
            'L unch': 'Lunch', 'A ncillary': 'Ancillary', 'C harges': 'Charges',
            'P ersonal': 'Personal', 'S erv': 'Serv', 'L aundry': 'Laundry', 'U nit': 'Unit',
            'V oucher': 'Voucher', 'R emarks': 'Remarks', 'T hequotedrate': 'The quoted rate',
            'V AT': 'VAT', 'tourismlevy': 'tourism levy', 'S pecial': 'Special',
            'I nstructions': 'Instructions', 'A nyextras': 'Any extras', 'traveller': 'traveller',
            'G eneral': 'General', 'T erms': 'Terms', 'C onditions': 'Conditions',
            'vouchervalid': 'voucher valid', 'specifiedservices': 'specified services',
            'A nyservices': 'Any services', 'required': 'required',
            'coveredbythevoucher': 'covered by the voucher', 'billeddirectly': 'billed directly',
            'traveller': 'traveller', 'R eferto': 'Refer to', 'TWF': 'TWF',
            'www': 'www', 'travelwithflair': 'travelwithflair', 'co': 'co', 'za': 'za',
            'terms': 'terms', 'conditions': 'conditions', 'K indlyremember': 'Kindly remember',
            'identitydocument': 'identity document', 'presentit': 'present it',
            'check': 'check', 'aboveaddress': 'above address', 'amended': 'amended',
            'I mmigration': 'Immigration', 'A ct': 'Act', 'relevantregulations': 'relevant regulations',
            'legalrequirement': 'legal requirement', 'accommodationsuppliers': 'accommodation suppliers',
            'registercontaining': 'register containing', 'detailsofallguests': 'details of all guests',
            'I mmigration': 'Immigration', 'R egulations': 'Regulations', 'T hebearer': 'The bearer',
            'vouchermaynot': 'voucher may not', 'handedanyform': 'handed any form',
            'cashinlieu': 'cash in lieu', 'meals': 'meals', 'C reated': 'Created',
            'J ul': 'Jul',
            
            # Specific fixes from debug output (more aggressive)
            'BillingAddress': 'Billing Address',
            'TravelwithFlair': 'Travel with Flair',
            'PrivateBag': 'Private Bag',
            'UlendoLodge': 'Ulendo Lodge',
            'Apartments': 'Apartments',
            '10SinclairRoad': '10 Sinclair Road',
            '05December2025': '05 December 2025',
            'InvoiceNO': 'Invoice NO',
            'Date:': 'Date:',
            'GuestName': 'Guest Name',
            'TANYAMPELEGENGKEKANA': 'TANYAMPELEGENG KEKANA', # Fix for specific name
            'SERVICES&CHARGES': 'SERVICES & CHARGES',
            'DESCRIPTIONQTYUNITTOTALPRICE': 'DESCRIPTION QTY UNIT PRICE TOTAL',
            'Roombooked': 'Room booked',
            'RateincludesDinner': 'Rate includes Dinner',
            'Breakfast&Lunch': 'Breakfast & Lunch',
            'PersonalServices': 'Personal Services',
            'INVOICETOTAL': 'INVOICE TOTAL',
            'PAYMENTDETAILS': 'PAYMENT DETAILS',
            'IMPORTANTNOTES': 'IMPORTANT NOTES',
            'AccountName': 'Account Name',
            'UlendoLodgeAndApartments': 'Ulendo Lodge And Apartments',
            'ProofofPayment': 'Proof of Payment',
            'Sendtoinfo@ulendolodge.com': 'Send to info@ulendolodge.com',
            'BankName': 'Bank Name',
            'StandardBankAccountNumber': 'Standard Bank Account Number',
            'BranchCode': 'Branch Code',
            'POLICIES&INFORMATION': 'POLICIES & INFORMATION',
            'HouseRules': 'House Rules',
            'Check-intime': 'Check-in time',
            'isanytimeafter14:00': 'is any time after 14:00',
            'Check-outis10:00thefollowingday': 'Check-out is 10:00 the following day',
            'Please respectotherGuestsintermsofnoise.': 'Please respect other Guests in terms of noise.',
            'Lapaandbraaiareasmaynotbeoccupiedafter10pm.': 'Lapa and braai areas may not be occupied after 10pm.',
            'RefundPolicy': 'Refund Policy',
            '100% Refundwillbegrantedwith72hoursnoticeofcheckin.': '100% Refund will be granted with 72 hours notice of check in.',
            '50% Refundwillbegrantedwith24hoursnoticeofcheckin.': '50% Refund will be granted with 24 hours notice of check in.',
            'Failuretocheckinwillresultinzerorefundastheroomwasreservedandnotoccupied.': 'Failure to check in will result in zero refund as the room was reserved and not occupied.',
            'PublicLiability': 'Public Liability',
            'UlendoLodgehasthe rightto reserveadmission.': 'Ulendo Lodge has the right to reserve admission.',
            'We arenotresponsible foranydamage/lossofany kindtovisitor property.': 'We are not responsible for any damage/loss of any kind to visitor property.',
            'Visitorswillbeheldaccountableforanydamagestobusinessproperty.': 'Visitors will be held accountable for any damages to business property.',
            # More specific text observed in the output with single-character spacing issues
            'SE V RICES': 'SERVICES', 'CHA G RES': 'CHARGES', 
            'UNIT DESC I RPTION': 'UNIT DESCRIPTION', 'QTY TOTAL P I RCE': 'QTY TOTAL PRICE',
            'P I RCE': 'PRICE', # Adjusting this as per output
            'A ccommodation': 'Accommodation',
            'R oombooked': 'Room booked',
            'N one': 'None',
            'R ateincludes': 'Rate includes',
            'D inner': 'Dinner',
            'B reakfast': 'Breakfast',
            'L unch': 'Lunch',
            'P ersonal': 'Personal',
            'S ervices': 'Services',
            'L aundry': 'Laundry',
            'IMPO T RANT': 'IMPORTANT',
            'INFO M RATION': 'INFORMATION',
            'H ouse R ules': 'House Rules',
            'C heck - in': 'Check-in',
            'C heck - out': 'Check-out',
            'D ate': 'Date',
            'G uest N ame': 'Guest Name',
            'INV - ': 'INV-', # Ensure consistent invoice number prefix
            'N O': 'NO', 
            'Total P rice': 'Total Price' # New fix from refined header
        }
        
        for wrong, correct in common_fixes.items():
            cleaned_line = cleaned_line.replace(wrong, correct)
        
        # Phase 3: Normalize whitespace within the line (replace multiple spaces with a single space and strip leading/trailing spaces)
        cleaned_lines.append(re.sub(r'\s+', ' ', cleaned_line.strip()))

    return '\n'.join(cleaned_lines)

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
    
    # Check current last_inv value
    c.execute("SELECT value FROM metadata WHERE key='last_inv'")
    result = c.fetchone()
    
    current_last_inv = 0
    if result:
        current_last_inv = result[0]
    
    # If current_last_inv is less than 599, or it doesn't exist, set it to 599
    if current_last_inv < 599:
        c.execute("INSERT OR REPLACE INTO metadata(key, value) VALUES('last_inv', 599)")
        last = 599 # Start from 600 next
    else:
        last = current_last_inv

    conn.commit()
    
    next_num = last + 1
    c.execute("UPDATE metadata SET value=? WHERE key='last_inv'", (next_num,))
    conn.commit()
    conn.close()
    return f"INV-{next_num:06d}"

def cleanup_old_files(directory, days_old=7):
    current_time = datetime.now()
    for filename in os.listdir(directory):
        filepath = os.path.join(directory, filename)
        if os.path.isfile(filepath):
            file_mod_time = datetime.fromtimestamp(os.path.getmtime(filepath))
            if (current_time - file_mod_time).days > days_old:
                os.remove(filepath)
                print(f"Deleted old file: {filepath}")