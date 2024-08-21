from flask import Flask, render_template, request
from office_tools.pdf_ops import PDFManipulation

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/process_pdf", methods=["POST"])
def process_pdf():
    if request.method == "POST":
        uploaded_file = request.files["pdf_file"]
        file_path = f"uploads/{uploaded_file.filename}"
        uploaded_file.save(file_path)

        # Create PDFManipulation object
        pdf_manipulation = PDFManipulation(file_path)

        # Choose the desired function (replace with your chosen function)
        extracted_text = pdf_manipulation.extract_text()

        return f"Extracted Text: {extracted_text}"

    return "Invalid request method"

if __name__ == "__main__":
    app.run(debug=True)
