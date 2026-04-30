import os
from PyPDF2 import PdfReader, PdfWriter, PdfMerger
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from pdfminer.high_level import extract_text
try:
    import fitz  # PyMuPDF
except Exception:  # pragma: no cover
    fitz = None
from PIL import Image  # Pillow
import io
try:
    import tabula
except Exception:  # pragma: no cover
    tabula = None


def _require_fitz():
    if fitz is None:
        raise ImportError("PyMuPDF is required for this operation. Install with: pip install PyMuPDF")


def _require_tabula():
    if tabula is None:
        raise ImportError("tabula-py is required for table extraction. Install with: pip install tabula-py")

class PDFAccess:
    def __init__(self, input_path="/inputs", output_path="/outputs"):
        self.input_path = input_path
        self.output_path = output_path
        os.makedirs(os.path.join( os.getcwd(),self.input_path), exist_ok=True)
        os.makedirs(os.path.join( os.getcwd(),self.output_path), exist_ok=True)

    def list_pdf_files(self, list_path=None):
        if list_path is None:
            list_path = self.input_path
        pdf_files = [filename for filename in os.listdir(list_path) if filename.endswith('.pdf')]

        if pdf_files:
            print("PDF files found:",*pdf_files, sep="\n")
        else:
            print("No PDF files found in the directory.")
        return pdf_files

    def read_pdf(self,file_name):
        file_path = os.path.join(self.input_path,file_name)
        pdf_file = PdfReader(file_path)
        return pdf_file

    def write_text_to_pdf(self, output_file_name, content, x = 100, y= 750 ):
        file_path = os.path.join(self.output_path, output_file_name)
        pdf_canvas = canvas.Canvas(file_path, pagesize=letter)
        pdf_canvas.drawString(x, y, content)
        pdf_canvas.save()
        return file_path

class PDF_Extract(PDFAccess):
    def __init__(self, input_path="/inputs", output_path="/outputs"):
        super().__init__(input_path, output_path)

    def complete_text_extract(self,file_name,pattern=None):
        file_path = os.path.join(self.input_path,file_name)
        text  =  extract_text(file_path)
        if pattern:
            matches  = pattern.findall(text)
            return matches
        else:
            return text

    def pagewise_text_extract(self,file_name,pattern=None,page_num=None):
        pdf_file = self.read_pdf(file_name)
        text_by_page = {}
        # If page_num is provided, extract text only from that page
        if page_num is not None:
            # Ensure page_num is within the valid range
            if 1 <= page_num <= len(pdf_file.pages):
                page = pdf_file.pages[page_num - 1]  # Convert to 0-based index
                text_by_page[page_num] = page.extract_text()
            else:
                raise ValueError("Page number out of range.")
        else:
            # Extract text from all pages
            for page_num in range(len(pdf_file.pages)):
                page = pdf_file.pages[page_num]
                text_by_page[page_num + 1] = page.extract_text()  # +1 to make page numbers 1-based

        return text_by_page

    def extract_images(self,file_name):
        _require_fitz()
        file_path = os.path.join(self.input_path,file_name)
        pdf_file = fitz.open(file_path)
        counter =1

        for i in range(len(pdf_file)):
            page = pdf_file[i]
            images = page.get_images()
            for image in images:
                base_img = pdf_file.extract_image(image[0])
                image_data = base_img["image"]
                img = Image.open(io.BytesIO(image_data))
                extension = base_img['ext']
                output_image_path = os.path.join(
                    self.output_path, f"image-{file_name}-{counter}.{extension}"
                )
                img.save(open(output_image_path,"wb"))
                counter +=1

    def extract_tables(self,file_name):
        _require_tabula()
        file_path = os.path.join(self.input_path,file_name)
        tables = tabula.read_pdf(file_path,pages = "all")
        print(tables)
        return tables

class PDF_Manipulate(PDFAccess):
    def __init__(self, input_path="/inputs", output_path="/outputs"):
        super().__init__(input_path, output_path)

    def merge_pdfs(self, merge_files_path=None, merge_dict=None,output_file_name='output_file'):

        if merge_dict is None:
            merge_dict = self.list_pdf_files(list_path=merge_files_path)
        pdf_merger = PdfMerger()
        for name in merge_dict:
            file_path = os.path.join(self.input_path, name)
            pdf_merger.append(file_path)
        with open(output_file_name+'.pdf', 'wb') as output:
            pdf_merger.write(output)

    def split_pdf_pages(self,split_file_name):
        try:
            pdf_file = self.read_pdf(split_file_name)
            for page_num in range(len(pdf_file.pages)):
                writer = PdfWriter()
                writer.add_page(pdf_file.pages[page_num])
                output_filename = f'{os.path.splitext(split_file_name)[0]}_page_{page_num + 1}.pdf'
                with open(output_filename, 'wb') as outfile:
                    writer.write(outfile)
                    print(f"Saved file: {output_filename}")
            print(f"Processed file: {split_file_name}")
        except Exception as e:
            print(f"Error processing file {split_file_name}: {e}")

    def move_empty_pdfs(self, empty_folder='./empty',delete=False):
        _require_fitz()
    # Ensure the empty_folder exists
        os.makedirs(empty_folder, exist_ok=True)
        file_list = self.list_pdf_files(list_path=self.input_path)
        for file_name in file_list:
            file_path = os.path.join(self.input_path, file_name)
            try:
                # Open the PDF file
                pdf_document = fitz.open(file_path)
                text_found = False
                # Iterate over each page to check for text
                for page_num in range(len(pdf_document)):
                    page = pdf_document[page_num]
                    text = page.get_text()
                    if text.strip():  # Check if there's any text
                        text_found = True
                        break
                pdf_document.close()

                if not text_found: # Move to the empty_folder or delete the empty PDF
                    if delete:
                        os.remove(file_path)
                        print(f"Deleted empty file: {file_name}")
                    else:
                        os.rename(file_path, os.path.join(empty_folder, file_name))
                        print(f"Moved empty file: {file_name}")
                else:
                    print(f"File {file_name} contains text")

            except Exception as e:
                print(f"Error processing file {file_name}: {e}")

    def sort_and_rename_files(self,rename=False):
        # Get all files in the folder and sort them alphabetically
        files = sorted([f for f in os.listdir(self.input_path) if os.path.isfile(os.path.join(self.input_path, f))])
        if rename:
        # Iterate over sorted files and rename them
            for index, filename in enumerate(files):
                new_filename = f"{index + 1:04d}_{filename}"
                old_path = os.path.join(self.input_path, filename)
                new_path = os.path.join(self.input_path, new_filename)
                os.rename(old_path, new_path)
                print(f"Renamed '{filename}' to '{new_filename}'")

    def combine_pdfs(self, output_filename, pdf_order):
        # Ensure the output folder exists
        os.makedirs(self.output_path, exist_ok=True)

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