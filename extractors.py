# extractors.py

#import re
import regex as re


import fitz
import pytesseract
from pdf2image import convert_from_path


# --------------------------
# YOUR ORIGINAL FUNCTION (UNTOUCHED)
# --------------------------
def pdf_to_text(pdf_path):
    doc = fitz.open(pdf_path)
    full_text = ""

    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        text = page.get_text("text")
        full_text += text + "\n"

        full_text_no_spaces = full_text.replace(" ", "").replace("\n", "")

    # If no text found → OCR fallback (added but doesn't change your logic)
    if len(full_text_no_spaces.strip()) < 30:
        print("⚠ Scanned PDF detected → OCR enabled.")
        full_text = ocr_pdf(pdf_path)
        full_text_no_spaces = full_text.replace(" ", "").replace("\n", "")

    return full_text, full_text_no_spaces


# --------------------------
# OCR (ADDED WITHOUT TOUCHING YOUR LOGIC)
# --------------------------
def ocr_pdf(path):
    images = convert_from_path(path)
    text = ""
    for img in images:
        text += pytesseract.image_to_string(img)
    return text


# --------------------------
# Extract allergens
# --------------------------
ALLERGENS = [
    "milk", "egg", "soy", "peanut", "fish", "gluten",
    "sesame", "mustard", "celery", "lupin"
]

def extract_allergens(text):
    found = []
    lower = text.lower()
    for a in ALLERGENS:
        if a in lower:
            found.append(a)
    return list(set(found))


# --------------------------
# Extract nutrition values
# --------------------------
#NUTRIENTS = {
    #"fat": r"(fat|zsír).*?(\d+\.?\d*)",
   # "protein": r"(protein|fehérje).*?(\d+\.?\d*)",
   # "carbs": r"(carb|carbohydrate|szénhidrát).*?(\d+\.?\d*)",
  #  "sodium": r"(salt|só).*?(\d+\.?\d*)",
 #   "energy": r"(energy|kcal|kj).*?(\d+\.?\d*)"
#}

NUTRIENTS = {
    "fat": r"\p{P}?\b(fat|zsír)\b\p{P}?\s*.*?(\d+[.,]?\d*)\s*(g|gram|mg|kg)?",
    "protein": r"\p{P}?\p{P}?\b(protein|fehérje)\b\p{P}?\s*.*?(\d+[.,]?\d*)\s*(g|gram|mg|kg)?",
    "carbs": r"\p{P}?\b(carb|carbohydrate|szénhidrát)\b\p{P}?\s*.*?(\d+[.,]?\d*)\s*(g|gram|mg|kg)?",
    "sugars": r"\p{P}?\b(sugar|cukor|cukrok)\b\p{P}?\s*.*?(\d+[.,]?\d*)\s*(g|gram|mg|kg)?",
    "sodium": r"\p{P}?\b(salt|só|sodium|nátrium)\b\p{P}?\s*.*?(\d+[.,]?\d*)\s*(g|gram|mg|kg|%)?",
    "energy": r"\p{P}?\b(energy|Energia|kcal|kj|kJ)\b\p{P}?\s*.*?(\d+[.,]?\d*)\s*(kcal|kj|kJ)?",
}

def extract_nutrition(text):
    lower = text.lower()
    results = {}
    for k, pattern in NUTRIENTS.items():
        match = re.search(pattern, lower)
        results[k] = match.group(2) if match else None
    return results
