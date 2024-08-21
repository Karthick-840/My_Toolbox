import os
from src.pdf_ops import PDF_Access,PDF_Extract, PDF_Manipulate


def main():
    input_path = r"C:\Users\gksme\PycharmProjects\sorting"

    # Uncomment the following lines to test each functionality

    # 1. PDF Access: List and read PDF files
    # pdf_access = PDF_Access(input_path=input_path)
    # pdf_files = pdf_access.list_pdf_files()
    # print(pdf_files)
    # pdf_file = pdf_access.read_pdf("2024 Overview.pdf")
    # print(pdf_file)

    # 2. PDF Extract: Extract text, tables, and images from PDF files
    # pdf_extract = PDF_Extract(input_path=input_path)
    # full_text = pdf_extract.complete_text_extract("2024 Overview.pdf")
    # print(full_text)
    # page_text = pdf_extract.pagewise_text_extract("October 26 Progress Report_Compressed 25MB.pdf", page_num=6)
    # print(page_text)
    # pattern = re.compile(r"[a-zA-Z]+,{1}\s{1}")
    # matches = pattern.findall(page_text)
    # names = [n[:-2] for n in matches]
    # print(names)
    # table = pdf_extract.extract_tables("2024 Overview.pdf")
    # print(table)
    # image = pdf_extract.extract_images("2024 Overview.pdf")
    # print(image)

    # 3. PDF Manipulate: Merge, split, and move PDF files
    # pdf_manipulate = PDF_Manipulate(input_path=input_path)
    # pdf_manipulate.merge_pdfs(merge_files_path=input_path)
    # pdf_manipulate.split_pdf_pages("2024 Overview.pdf")
    # pdf_manipulate.move_empty_pdfs(empty_folder="./outputs", delete=False)

if __name__ == "__main__":
    main()