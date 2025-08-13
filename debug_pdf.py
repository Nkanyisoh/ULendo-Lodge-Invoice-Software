#!/usr/bin/env python3
"""
Debug script to test PDF parsing functionality
"""

import os
from invoice_generator import parse_voucher_pdf

def test_pdf_parsing():
    """Test PDF parsing with the uploaded voucher"""
    pdf_path = "uploads/D231745T1B1C18015138328Voucher-G838867-MICHAELLMASILELA (1).pdf"
    
    if os.path.exists(pdf_path):
        print("Testing PDF parsing...")
        print(f"PDF file: {pdf_path}")
        print("=" * 50)
        
        try:
            data = parse_voucher_pdf(pdf_path)
            print("\nParsing completed successfully!")
            print("=" * 50)
            print("EXTRACTED DATA SUMMARY:")
            for key, value in data.items():
                print(f"{key}: {value}")
        except Exception as e:
            print(f"Error parsing PDF: {e}")
    else:
        print(f"PDF file not found: {pdf_path}")
        print("Available files in uploads directory:")
        if os.path.exists("uploads"):
            for file in os.listdir("uploads"):
                print(f"  - {file}")

if __name__ == "__main__":
    test_pdf_parsing()
