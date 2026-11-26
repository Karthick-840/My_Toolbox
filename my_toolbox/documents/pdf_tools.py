import hashlib
import os
import re
import shutil
from pathlib import Path

from pdfminer.high_level import extract_text
from PyPDF2 import PdfMerger, PdfReader, PdfWriter
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

try:
    import fitz  # PyMuPDF
except Exception:  # pragma: no cover
    fitz = None
import io

from PIL import Image  # Pillow

try:
    import tabula
except Exception:  # pragma: no cover
    tabula = None


IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}


def _natural_key(path):
    """Sort key so 'img2' comes before 'img10'."""
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", Path(path).name)]


def _to_rgb(img):
    """Return an RGB image; transparency is flattened onto white."""
    has_alpha = img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info)
    if has_alpha:
        rgba = img.convert("RGBA")
        background = Image.new("RGB", rgba.size, (255, 255, 255))
        background.paste(rgba, mask=rgba.getchannel("A"))
        return background
    return img if img.mode == "RGB" else img.convert("RGB")


def _load_image(item):
    """Accept PIL.Image, BytesIO, bytes, or a file path (str / Path)."""
    if isinstance(item, Image.Image):
        img = item
    elif isinstance(item, (bytes, bytearray)):
        img = Image.open(io.BytesIO(item))
    elif isinstance(item, io.BytesIO):
        item.seek(0)
        img = Image.open(item)
    elif isinstance(item, (str, Path)):
        img = Image.open(Path(item).expanduser())
    else:
        raise TypeError(f"Unsupported image type: {type(item).__name__}")
    img.load()
    return _to_rgb(img)


def _parse_page_ranges(spec, total):
    """Turn '3-7,10,12-' into a list of 0-based page indexes (order preserved, 1-based input)."""
    pages = []
    for part in re.split(r"\s*,\s*", (spec or "").strip()):
        if not part:
            continue
        m = re.fullmatch(r"(\d+)?\s*-\s*(\d+)?", part) if "-" in part else None
        if m:
            start = int(m.group(1) or 1)
            end = int(m.group(2) or total)
        elif part.isdigit():
            start = end = int(part)
        else:
            raise ValueError(f"Invalid page range: '{part}'")
        if start < 1 or end < start or end > total:
            raise ValueError(f"Page range '{part}' is outside 1-{total}")
        pages.extend(range(start - 1, end))
    if not pages:
        raise ValueError("No pages selected.")
    return pages


def _require_fitz():
    if fitz is None:
        raise ImportError("PyMuPDF is required for this operation. Install with: pip install PyMuPDF")


def _require_tabula():
    if tabula is None:
        raise ImportError("tabula-py is required for table extraction. Install with: pip install tabula-py")

class PDFAccess:
    def __init__(self, input_path="inputs", output_path="outputs"):
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


    #TODO:The Upgrade: Add a method to detect if a PDF is a "Scan" vs a "Digital" PDF. If page.get_text() is empty but page.get_images() is not, move it to an /ocr_queue folder.
    def needs_ocr(self, file_name):
        """Returns True if the PDF has images but no selectable text."""
        _require_fitz()
        doc = fitz.open(os.path.join(self.input_path, file_name))
        for page in doc:
            if not page.get_text().strip() and len(page.get_images()) > 0:
                return True
        return False

    #TODO: Feature,Class,Benefit
    # MD5 Hashing,PDFAccess,Prevents merging the same document multiple times.
    # Password Vault,PDF_Security,Automates the unlocking of recurring monthly statements.
    # OCR Redirect,PDF_Extract,Identifies documents that need a scanner tool before text extraction.
    # Metadata Stripper,PDF_Manipulate,Removes author/creator info before sharing files externally.

    @staticmethod
    def move_duplicates_by_hash(directory, duplicates_subdir="duplicates"):

        def file_md5(filepath, chunk_size=8192):
            hash_md5 = hashlib.md5()
            with open(filepath, "rb") as f:
                for chunk in iter(lambda: f.read(chunk_size), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()

        hashes = {}
        duplicates_dir = os.path.join(directory, duplicates_subdir)
        os.makedirs(duplicates_dir, exist_ok=True)

        for root, _, files in os.walk(directory):
            for filename in files:
                filepath = os.path.join(root, filename)
                file_hash = file_md5(filepath)
                if file_hash in hashes:
                    dest_path = os.path.join(duplicates_dir, filename)
                    # Ensure unique filename in duplicates folder
                    base, ext = os.path.splitext(filename)
                    count = 1
                    while os.path.exists(dest_path):
                        dest_path = os.path.join(duplicates_dir, f"{base}_dup{count}{ext}")
                        count += 1
                    shutil.move(filepath, dest_path)
                    print(f"Moved duplicate: {filepath} -> {dest_path}")
                else:
                    hashes[file_hash] = filepath

class PDF_Extract(PDFAccess):
    def __init__(self, input_path="inputs", output_path="outputs"):
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
        saved = []

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
                with open(output_image_path, "wb") as fh:
                    img.save(fh, format=img.format)
                saved.append(output_image_path)
                counter +=1
        pdf_file.close()
        return saved

    def extract_tables(self,file_name):
        _require_tabula()
        file_path = os.path.join(self.input_path,file_name)
        tables = tabula.read_pdf(file_path,pages = "all")
        print(tables)
        return tables

class PDF_Manipulate(PDFAccess):
    def __init__(self, input_path="inputs", output_path="outputs"):
        super().__init__(input_path, output_path)

    def merge_pdfs(self, merge_files_path=None, merge_dict=None,output_file_name='output_file'):

        if merge_dict is None:
            merge_dict = self.list_pdf_files(list_path=merge_files_path)
        pdf_merger = PdfMerger()
        for name in merge_dict:
            file_path = os.path.join(self.input_path, name)
            pdf_merger.append(file_path)
        output_path = os.path.join(self.output_path, output_file_name + '.pdf')
        with open(output_path, 'wb') as output:
            pdf_merger.write(output)
        pdf_merger.close()
        return output_path

    def split_pdf_pages(self,split_file_name):
        saved = []
        try:
            pdf_file = self.read_pdf(split_file_name)
            for page_num in range(len(pdf_file.pages)):
                writer = PdfWriter()
                writer.add_page(pdf_file.pages[page_num])
                output_filename = os.path.join(
                    self.output_path, f'{os.path.splitext(split_file_name)[0]}_page_{page_num + 1}.pdf'
                )
                with open(output_filename, 'wb') as outfile:
                    writer.write(outfile)
                    print(f"Saved file: {output_filename}")
                saved.append(output_filename)
            print(f"Processed file: {split_file_name}")
        except Exception as e:
            print(f"Error processing file {split_file_name}: {e}")
        return saved

    def move_empty_pdfs(self, empty_folder='./empty',delete=False):
        _require_fitz()
    # Ensure the empty_folder exists
        os.makedirs(empty_folder, exist_ok=True)
        file_list = self.list_pdf_files(list_path=self.input_path)
        empty_files = []
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
                    empty_files.append(file_name)
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
        return empty_files

    def extract_pages(self, file_name, page_ranges, output_file_name=None):
        """Save selected pages (1-based, e.g. '3-7,10,12-') into a new PDF in output_path."""
        reader = self.read_pdf(file_name)
        indexes = _parse_page_ranges(page_ranges, len(reader.pages))
        writer = PdfWriter()
        for i in indexes:
            writer.add_page(reader.pages[i])
        stem = os.path.splitext(file_name)[0]
        output_file_name = output_file_name or f"{stem}_pages.pdf"
        if not output_file_name.lower().endswith(".pdf"):
            output_file_name += ".pdf"
        output_path = os.path.join(self.output_path, output_file_name)
        with open(output_path, "wb") as fh:
            writer.write(fh)
        return output_path

    def remove_blank_pages(self, file_name, output_file_name=None, check_images=True):
        """Write a copy of the PDF without pages that have no text (and no images if check_images).

        Returns (output_path, removed_page_numbers); output_path is None if every page is blank.
        """
        _require_fitz()
        file_path = os.path.join(self.input_path, file_name)
        doc = fitz.open(file_path)
        try:
            keep, removed = [], []
            for i, page in enumerate(doc):
                blank = not page.get_text().strip()
                if blank and check_images:
                    blank = not page.get_images()
                (removed if blank else keep).append(i)
        finally:
            doc.close()
        removed_pages = [i + 1 for i in removed]
        if not keep:
            return None, removed_pages

        reader = self.read_pdf(file_name)
        writer = PdfWriter()
        for i in keep:
            writer.add_page(reader.pages[i])
        stem = os.path.splitext(file_name)[0]
        output_file_name = output_file_name or f"{stem}_noblank.pdf"
        if not output_file_name.lower().endswith(".pdf"):
            output_file_name += ".pdf"
        output_path = os.path.join(self.output_path, output_file_name)
        with open(output_path, "wb") as fh:
            writer.write(fh)
        return output_path, removed_pages

    def sort_and_rename_files(self,rename=False):
        # Get all files in the folder and sort them alphabetically
        files = sorted([f for f in os.listdir(self.input_path) if os.path.isfile(os.path.join(self.input_path, f))])
        if not rename:
            return files
        renamed = []
        for index, filename in enumerate(files):
            new_filename = f"{index + 1:04d}_{filename}"
            old_path = os.path.join(self.input_path, filename)
            new_path = os.path.join(self.input_path, new_filename)
            os.rename(old_path, new_path)
            print(f"Renamed '{filename}' to '{new_filename}'")
            renamed.append(new_filename)
        return renamed

    def combine_pdfs(self, output_filename, pdf_order):
        # Ensure the output folder exists
        os.makedirs(self.output_path, exist_ok=True)
        written = []

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
            written.append(output_path)
            print(f"Created {output_filename}.pdf")
        return written


class PDF_FromImages(PDFAccess):
    """Build PDFs from images (files, bytes, BytesIO or PIL images)."""

    def images_to_pdf(self, images, output_file_name, resolution=100.0):
        """Save images, in the given order, as one multi-page PDF; returns the output path."""
        pages = [_load_image(i) for i in images]
        if not pages:
            raise ValueError("No images provided.")
        if not output_file_name.lower().endswith(".pdf"):
            output_file_name += ".pdf"

        out = Path(os.path.join(self.output_path, output_file_name)).expanduser().resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        pages[0].save(
            out,
            format="PDF",
            save_all=True,
            append_images=pages[1:],
            resolution=resolution,
            quality=100,
        )
        return str(out)

    def folder_to_pdf(self, folder_path, output_file_name, resolution=100.0):
        """Combine all supported images in a folder (natural filename order) into one PDF."""
        folder = Path(folder_path).expanduser()
        if not folder.is_dir():
            raise NotADirectoryError(f"Not a folder: {folder}")
        files = sorted(
            (p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS),
            key=_natural_key,
        )
        if not files:
            raise FileNotFoundError(
                f"No supported images ({', '.join(sorted(IMAGE_EXTENSIONS))}) in {folder}"
            )
        return self.images_to_pdf([str(f) for f in files], output_file_name, resolution)



class PDF_Security(PDFAccess):
    def check_encryption(self, file_name):
        reader = self.read_pdf(file_name)
        return reader.is_encrypted

    def unlock_with_vault(self, file_name, password_list):
        """Attempts to unlock a PDF using a list of known passwords."""
        file_path = os.path.join(self.input_path, file_name)
        for pwd in password_list:
            try:
                reader = PdfReader(file_path)
                if reader.decrypt(pwd):
                    # Logic to save the unlocked version and delete the locked one
                    self.logger.info(f"Successfully unlocked {file_name}")
                    return True
            except Exception:
                continue
        return False
