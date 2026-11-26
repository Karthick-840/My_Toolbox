import os

from my_toolbox.documents.pdf_tools import PDF_Extract, PDF_Manipulate, PDFAccess


def _make_pdf(path, text):
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas

    c = canvas.Canvas(str(path), pagesize=letter)
    c.drawString(100, 750, text)
    c.save()


def test_pdf_access_list_read_write(tmp_path):
    in_dir = tmp_path / "inputs"
    out_dir = tmp_path / "outputs"
    in_dir.mkdir()
    out_dir.mkdir()

    pdf = in_dir / "a.pdf"
    _make_pdf(pdf, "hello")

    acc = PDFAccess(input_path=str(in_dir), output_path=str(out_dir))
    found = acc.list_pdf_files(list_path=str(in_dir))
    assert "a.pdf" in found

    reader = acc.read_pdf("a.pdf")
    assert len(reader.pages) >= 1

    out_file = acc.write_text_to_pdf("x.pdf", "text")
    assert os.path.exists(out_file)


def test_pdf_extract_pagewise_and_complete(tmp_path):
    in_dir = tmp_path / "inputs"
    out_dir = tmp_path / "outputs"
    in_dir.mkdir()
    out_dir.mkdir()

    pdf = in_dir / "b.pdf"
    _make_pdf(pdf, "world")

    ext = PDF_Extract(input_path=str(in_dir), output_path=str(out_dir))
    by_page = ext.pagewise_text_extract("b.pdf")
    assert 1 in by_page

    page_one = ext.pagewise_text_extract("b.pdf", page_num=1)
    assert 1 in page_one

    txt = ext.complete_text_extract("b.pdf")
    assert isinstance(txt, str)


def test_pdf_manipulate_merge_split_sort(tmp_path):
    in_dir = tmp_path / "inputs"
    out_dir = tmp_path / "outputs"
    in_dir.mkdir()
    out_dir.mkdir()

    p1 = in_dir / "a.pdf"
    p2 = in_dir / "b.pdf"
    _make_pdf(p1, "one")
    _make_pdf(p2, "two")

    man = PDF_Manipulate(input_path=str(in_dir), output_path=str(out_dir))
    cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        man.merge_pdfs(merge_dict=["a.pdf", "b.pdf"], output_file_name="merged")
        assert (out_dir / "merged.pdf").exists()

        man.split_pdf_pages("a.pdf")
        assert (out_dir / "a_page_1.pdf").exists()

        man.sort_and_rename_files(rename=True)
        renamed = list(in_dir.glob("*.pdf"))
        assert any(f.name.startswith("0001_") for f in renamed)
    finally:
        os.chdir(cwd)


def test_pdf_from_images_and_folder(tmp_path):
    from PIL import Image

    from my_toolbox.documents.pdf_tools import PDF_FromImages

    img_dir = tmp_path / "imgs"
    img_dir.mkdir()
    for n in ("img10", "img2"):
        Image.new("RGBA", (20, 20), (255, 0, 0, 0)).save(img_dir / f"{n}.png")

    tool = PDF_FromImages(input_path=str(tmp_path / "in"), output_path=str(tmp_path / "out"))
    out = tool.folder_to_pdf(str(img_dir), "combined")
    assert out.endswith("combined.pdf")
    from PyPDF2 import PdfReader

    assert len(PdfReader(out).pages) == 2


def _three_page_pdf(path, blank_middle=True):
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas

    c = canvas.Canvas(str(path), pagesize=letter)
    c.drawString(100, 750, "page one")
    c.showPage()
    if not blank_middle:
        c.drawString(100, 750, "page two")
    c.showPage()
    c.drawString(100, 750, "page three")
    c.save()


def test_extract_pages_and_remove_blank(tmp_path):
    import pytest
    from PyPDF2 import PdfReader

    in_dir, out_dir = tmp_path / "in", tmp_path / "out"
    in_dir.mkdir()
    _three_page_pdf(in_dir / "doc.pdf")
    man = PDF_Manipulate(input_path=str(in_dir), output_path=str(out_dir))

    out = man.extract_pages("doc.pdf", "3, 1-2")
    texts = [p.extract_text().strip() for p in PdfReader(out).pages]
    assert texts[0] == "page three" and len(texts) == 3
    with pytest.raises(ValueError):
        man.extract_pages("doc.pdf", "2-9")

    cleaned, removed = man.remove_blank_pages("doc.pdf")
    assert removed == [2]
    assert len(PdfReader(cleaned).pages) == 2
