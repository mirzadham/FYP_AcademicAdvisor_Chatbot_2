import PyPDF2
import sys

def convert_pdf_to_txt(pdf_path, txt_path):
    """Convert PDF file to TXT format."""
    try:
        # Open the PDF file
        with open(pdf_path, 'rb') as pdf_file:
            # Create PDF reader object
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            # Extract text from all pages
            text_content = []
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text_content.append(page.extract_text())
            
            # Join all pages
            full_text = '\n\n'.join(text_content)
            
            # Write to text file
            with open(txt_path, 'w', encoding='utf-8') as txt_file:
                txt_file.write(full_text)
            
            print(f"Successfully converted {pdf_path} to {txt_path}")
            print(f"Total pages processed: {len(pdf_reader.pages)}")
            
    except Exception as e:
        print(f"Error converting PDF: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    pdf_path = r"c:\RasaBot\data\handbook\pdf\spe.pdf"
    txt_path = r"c:\RasaBot\data\handbook\txt\spe.txt"
    
    convert_pdf_to_txt(pdf_path, txt_path)
