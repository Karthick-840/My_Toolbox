import os

from my_toolbox.pdf_tools import PDF_Extract, PDF_Manipulate, PDFAccess


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
        assert (tmp_path / "merged.pdf").exists()

        man.split_pdf_pages("a.pdf")
        assert (tmp_path / "a_page_1.pdf").exists()

        man.sort_and_rename_files(rename=True)
        renamed = list(in_dir.glob("*.pdf"))
        assert any(f.name.startswith("0001_") for f in renamed)
    finally:
        os.chdir(cwd)
