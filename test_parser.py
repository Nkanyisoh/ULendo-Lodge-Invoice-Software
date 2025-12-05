#!/usr/bin/env python3
"""
Test script for the new PyPDF2-based voucher parser
"""

import os
from voucher_parser import parse_voucher_pdf

def test_parser():
    """Test the voucher parser with uploaded PDFs"""
    uploads_dir = "uploads"
    
    if not os.path.exists(uploads_dir):
        print("Uploads directory not found")
        return
    
    pdf_files = [f for f in os.listdir(uploads_dir) if f.endswith('.pdf')]
    
    if not pdf_files:
        print("No PDF files found in uploads directory")
        return
    
    print(f"Found {len(pdf_files)} PDF file(s):")
    for pdf_file in pdf_files:
        print(f"  - {pdf_file}")
    
    print("\n" + "="*50)
    
    # Test the first PDF file
    test_pdf = pdf_files[0]
    pdf_path = os.path.join(uploads_dir, test_pdf)
    
    print(f"Testing parser with: {test_pdf}")
    print("="*50)
    
    try:
        # Parse the PDF
        result = parse_voucher_pdf(pdf_path)
        
        if result:
            print("\n✅ Parsing successful!")
            print("\n=== EXTRACTED DATA ===")
            
            # Print key information
            print(f"Voucher Number: {result.get('voucher_number', 'N/A')}")
            print(f"Passenger Name: {result.get('passenger_names', 'N/A')}")
            print(f"Check-in: {result.get('check_in', 'N/A')}")
            print(f"Check-out: {result.get('check_out', 'N/A')}")
            print(f"Length of Stay: {result.get('length_of_stay', 'N/A')} days")
            print(f"Description: {result.get('description', 'N/A')}")
            print(f"Rate: R{result.get('rate_incl', 'N/A')}")
            print(f"Total: R{result.get('max_total', 'N/A')}")
            print(f"Ancillary: {result.get('ancillary_description', 'N/A')}")
            print(f"Ancillary Amount: R{result.get('ancillary_charges', 'N/A')}")
            
            print(f"\nLine Items: {len(result.get('line_items', []))}")
            for i, item in enumerate(result.get('line_items', [])):
                print(f"  {i+1}. {item.get('description', 'N/A')}")
                print(f"     Qty: {item.get('qty', 'N/A')}, Rate: R{item.get('unit_price', 'N/A')}, Total: R{item.get('total', 'N/A')}")
            
            print(f"\nInvoice Total: R{result.get('invoice_total', 'N/A')}")
            
        else:
            print("\n❌ Parsing failed!")
            
    except Exception as e:
        print(f"\n❌ Error during parsing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_parser()
