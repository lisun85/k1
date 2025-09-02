from extractor import K1Extractor

def main():
    print("Running K1 PDF Diagnostic...")
    
    # Create extractor instance
    extractor = K1Extractor(verbose=True)
    
    # Path to your PDF file
    pdf_path = "Input/Input_Enviva_Sample_Tax_Package_10000_units-2.pdf"
    
    # Run diagnostic
    extractor.diagnose_pdf_extraction(pdf_path)
if __name__ == "__main__":
    main()
