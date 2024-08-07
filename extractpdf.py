import fitz  #pymupdf

def extract_text_from_pdf(pdf_path):
    try:
        pdf_document = fitz.open(pdf_path)
        
        extracted_text = """ """

        for page_num in range(len(pdf_document)):
            
            page = pdf_document.load_page(page_num)
        
            text = page.get_text()
    
            extracted_text += text + "\n"

        pdf_document.close()

        return extracted_text.strip()
    except Exception as e:
        print(f"An error occurred while extracting text from PDF: {e}")
        return None

# Example usage
#pdf_path = "C:/Users/Alwin/Downloads/senior-software-developer - Template 16.pdf"
#pdf_content = extract_text_from_pdf(pdf_path)
#print(pdf_content)