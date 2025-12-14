import re

def remove_page_numbers(input_file, output_file):
    """Remove page numbers from the text file."""
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Split into lines
        lines = content.split('\n')
        
        cleaned_lines = []
        for line in lines:
            # Remove standalone page numbers at the beginning of lines
            # Pattern: line starts with digits followed by 2+ spaces and then text
            # This catches patterns like "52  SINOPSIS", "53  ECN3113", etc.
            cleaned_line = re.sub(r'^\d+\s\s+', '', line)
            cleaned_lines.append(cleaned_line)
        
        # Join lines back
        cleaned_content = '\n'.join(cleaned_lines)
        
        # Write cleaned content
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(cleaned_content)
        
        print(f"Successfully removed page numbers from {input_file}")
        print(f"Cleaned file saved to: {output_file}")
        
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    input_file = r"c:\RasaBot\data\handbook\txt\spe.txt"
    output_file = r"c:\RasaBot\data\handbook\txt\spe.txt"
    
    remove_page_numbers(input_file, output_file)
