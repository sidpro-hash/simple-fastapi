from fastapi import FastAPI, File, UploadFile, HTTPException, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from typing import List
from pathlib import Path
import PyPDF2

app = FastAPI()

# Configuration
UPLOAD_FOLDER = Path('./uploads')
UPLOAD_FOLDER.mkdir(exist_ok=True)  # Ensure the folder exists

# Template Configuration
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", response_class=HTMLResponse)
def render_upload_page(request: Request):
    return templates.TemplateResponse("upload.html", {"request": request})


@app.post("/upload-pdf")
def upload_pdf(file: UploadFile = File(...)):

    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="File is not a PDF")

    file_path = UPLOAD_FOLDER / file.filename

    try:
        with file_path.open("wb") as temp_file:
            temp_file.write(file.file.read())

        extracted_text = extract_text_from_pdf(file_path)
        file_path.unlink()  # Clean up

        return {"filename": file.filename, "text": extracted_text}

    except Exception as e:
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(status_code=500, detail=f"Failed to process the file: {str(e)}")


@app.post("/upload-pdfs")
def upload_pdfs(files: List[UploadFile] = File(...)):

    responses = []

    for file in files:
        if not file.filename.lower().endswith('.pdf'):
            responses.append({"filename": file.filename, "error": "File is not a PDF"})
            continue

        file_path = UPLOAD_FOLDER / file.filename

        try:
            with file_path.open("wb") as temp_file:
                temp_file.write(file.file.read())

            extracted_text = extract_text_from_pdf(file_path)
            file_path.unlink()  # Clean up

            responses.append({"filename": file.filename, "text": extracted_text})

        except Exception as e:
            if file_path.exists():
                file_path.unlink()
            responses.append({"filename": file.filename, "error": f"Failed to process: {str(e)}"})

    return responses


def extract_text_from_pdf(file_path: Path) -> str:
    """
    Extracts text from a PDF file.
    """
    text = ""
    with file_path.open('rb') as pdf_file:
        reader = PyPDF2.PdfReader(pdf_file)
        for page in reader.pages:
            text += page.extract_text()
    return text.strip()
