# main.py

import os
import tempfile

from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware

from extractors import pdf_to_text, extract_allergens, extract_nutrition

#from pdf_nutrients_extraction import pdf_to_text, extract_allergens, extract_nutrition

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://front-end-pdf-extractor.vercel.app"],  # or your domain
    #allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/extract")
async def extract(file: UploadFile = File(...)):
    # Save uploaded PDF temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    # Use your original logic
    full_text, full_text_no_spaces = pdf_to_text(tmp_path)

    allergens = extract_allergens(full_text)
    nutrition = extract_nutrition(full_text)

    os.remove(tmp_path)

    return {
        "allergens": allergens,
        "nutrition": nutrition,
        "raw_text": full_text[:500],     # preview
        "raw_text_no_spaces": full_text_no_spaces[:500]
    }
