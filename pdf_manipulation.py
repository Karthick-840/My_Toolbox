import os
from PyPDF2 import PdfReader, PdfWriter
from PIL import Image
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


class PDFManipulation:
    def __init__(self, input_path, output_path):
        self.input_path = input_path
        self.output_path = output_path
        os.makedirs(self.output_path, exist_ok=True)
        os.makedirs(self.input_path, exist_ok=True)


    def read_pdf(self):
        with open(self.file_path, 'rb') as pdf_file:
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            return pdf_reader

    def extract_text(self):
        pdf_reader = self.read_pdf()
        text = ""
        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            text += page.extract_text()
        return text

    def merge_pdfs(self, input_files, output_file):
        pdf_merger = PyPDF2.PdfMerger()
        for pdf in input_files:
            pdf_merger.append(pdf)
        with open(output_file, 'wb') as output:
            pdf_merger.write(output)
            
    def split_pdf_pages(self):
    # Iterate over all files in the input folder
        for filename in os.listdir(self.input_path ):
            if filename.endswith('.pdf'):
                input_path = os.path.join(self.input_path , filename)
                try:
                    reader = PdfReader(input_path)
                    for page_num in range(len(reader.pages)):
                        writer = PdfWriter()
                        writer.add_page(reader.pages[page_num])

                        output_filename = f'{os.path.splitext(filename)[0]}_page_{page_num + 1}.pdf'
                        output_path = os.path.join(self.output_path , output_filename)
                        with open(output_path, 'wb') as outfile:
                            writer.write(outfile)
                    print(f"Processed file: {filename}")
                except Exception as e:
                    print(f"Error processing file {filename}: {e}")
            
            
    def sort_and_rename_files(self,rename=False):
    # Get all files in the folder and sort them alphabetically
        files = sorted([f for f in os.listdir(self.input_path) if os.path.isfile(os.path.join(self.input_path, f))])

        if rename:
        # Iterate over sorted files and rename them
            for index, filename in enumerate(files):
                file_extension = os.path.splitext(filename)[1]
                new_filename = f"{index + 1:04d}_{filename}"
                old_path = os.path.join(folder_path, filename)
                new_path = os.path.join(folder_path, new_filename)
                os.rename(old_path, new_path)
                print(f"Renamed '{filename}' to '{new_filename}'")

    def combine_pdfs(self, output_filename, pdf_order):
        # Ensure the output folder exists
        os.makedirs(output_folder, exist_ok=True)
        
        for output_filename, file_sequence in pdf_order.items():
            writer = PdfWriter()
            
            for prefix in file_sequence:
                prefix_str = f"{prefix:04d}_"
                print(prefix_str)
                # Find the file that starts with the current prefix
                input_filename = next((f for f in os.listdir(self.input_path) if f.startswith(prefix_str)), None)
                if input_filename:
                    input_path = os.path.join(self.input_path, input_filename)
                    reader = PdfReader(input_path)
                    for page_num in range(len(reader.pages)):
                        writer.add_page(reader.pages[page_num])
                else:
                    print(f"File not found for prefix: {prefix_str}")
            
            output_path = os.path.join(self.output_path, f"{output_filename}.pdf")
            with open(output_path, 'wb') as output_file:
                writer.write(output_file)
            print(f"Created {output_filename}.pdf")
            
            
    def move_empty_pdfs(input_folder, empty_folder):
    # Ensure the empty_folder exists
    os.makedirs(empty_folder, exist_ok=True)

    # Iterate over all files in the input folder
    for filename in os.listdir(input_folder):
        if filename.endswith('.pdf'):
            input_path = os.path.join(input_folder, filename)
            try:
                # Open the PDF file
                pdf_document = fitz.open(input_path)
                text_found = False

                # Iterate over each page to check for text
                for page_num in range(len(pdf_document)):
                    page = pdf_document[page_num]
                    text = page.get_text()
                    if text.strip():  # Check if there's any text
                        text_found = True
                        break

                pdf_document.close()  # Explicitly close the PDF file

                if not text_found:
                    # Move the empty PDF to the empty_folder
                    shutil.move(input_path, os.path.join(empty_folder, filename))
                    print(f"Moved empty file: {filename}")
                else:
                    print(f"File {filename} contains text")

            except Exception as e:
                print(f"Error processing file {filename}: {e}")



