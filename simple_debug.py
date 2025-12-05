#!/usr/bin/env python3
"""
Simple debug script to test PDF text extraction
"""

import pdfplumber
import os

def test_pdf_extraction():
    """Test PDF text extraction"""
    pdf_path = "uploads/D231745T1B1C18015138328Voucher-G838867-MICHAELLMASILELA (1).pdf"
    
    if os.path.exists(pdf_path):
        print("Testing PDF text extraction...")
        print(f"PDF file: {pdf_path}")
        print("=" * 50)
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                text = pdf.pages[0].extract_text()
                
            print("=== EXTRACTED PDF TEXT ===")
            print(text)
            print("=== END EXTRACTED TEXT ===")
            
            lines = text.split('\n')
            print(f"\nTotal lines extracted: {len(lines)}")
            print("\n=== LINE BY LINE ANALYSIS ===")
            
            for i, line in enumerate(lines):
                line = line.strip()
                print(f"Line {i}: '{line}'")
                
                # Look for specific keywords
                keywords = [
                    'Passenger', 'Voucher', 'Check-in', 'Check-out', 
                    'Length', 'Description', 'UOM', 'Qty', 'Rate', 
                    'Total', 'Ancillary', 'Currency'
                ]
                
                for keyword in keywords:
                    if keyword.lower() in line.lower():
                        print(f"  -> Found keyword '{keyword}' in line {i}")
                        
        except Exception as e:
            print(f"Error extracting PDF text: {e}")
    else:
        print(f"PDF file not found: {pdf_path}")
        print("Available files in uploads directory:")
        if os.path.exists("uploads"):
            for file in os.listdir("uploads"):
                print(f"  - {file}")

if __name__ == "__main__":
    test_pdf_extraction()
