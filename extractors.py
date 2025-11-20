# extractors.py
import openai
#import re
import regex as re
#from google.cloud import vision--you failed me
import os
from openai import OpenAI

from PIL import Image
import io
import base64
import fitz
#import pytesseract --- not supported on vercel and too many dependencies failing to install
from pdf2image import convert_from_path

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key = OPENAI_API_KEY)    

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
        full_text = ocr_pdf_with_llm(pdf_path)
        full_text_no_spaces = full_text.replace(" ", "").replace("\n", "")

    return full_text, full_text_no_spaces


# --------------------------
# OCR using Google vision.
#tesseract failed and has dependencies issues on vercel
# --------------------------
# this approach is billable and on google, so will cut it out and use an LLm
'''
def ocr_pdf_with_google_vision(pdf_path):
    """
    OCR fallback for scanned PDFs using Google Cloud Vision API.
    Uses PyMuPDF to rasterize each page → image → send to Vision.
    """
    client = vision.ImageAnnotatorClient()
    doc = fitz.open(pdf_path)
    full_text = ""

    for page in doc:
        # Render page as PNG
        pix = page.get_pixmap()
        img_bytes = pix.tobytes("png")

        # Convert to Vision API Image object
        image = vision.Image(content=img_bytes)

        # Run OCR
        response = client.document_text_detection(image=image)

        if response.error.message:
            raise Exception(f"Google Vision API Error: {response.error.message}")

        full_text += response.full_text_annotation.text + "\n"

    return full_text
 '''
###----
#using gpt open ai api to extract text
##----

def ocr_pdf_with_llm(pdf_path):
    """
    OCR fallback using an LLM (OpenAI Vision API).
    Renders each PDF page as an image, sends to LLM, extracts text.
    """
    doc = fitz.open(pdf_path)
    full_text = ""

    for page in doc:
        # Render page to PNG bytes
        pix = page.get_pixmap()
        img_bytes = pix.tobytes("png")

        # Encode image to base64
        b64_image = base64.b64encode(img_bytes).decode()

        # Ask LLM to extract ONLY text
        response = client.chat.completions.create(
            model="gpt-5.1",  # cheap & fast for OCR
            #model = "o4-mini",
            # will use a prompt to pull out the allergens and also extract texts

            #prompt = "Extract all the text exactly as it appears on this page."

            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Extract all the text exactly as it appears on this page"},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{b64_image}"
                            }
                        }
                    ]
                }
            ],
           # max_tokens=2048 #chatgpt5.1 does not accept token limits and support image processing unlike gpt4.0 models
           # the new LLM api now does not support text tume for image processing, used image_url as type
        )

        #page_text = response.choices[0].message["content"]
        page_text = response.choices[0].message.content
        full_text += page_text + "\n"

    return full_text


# --------------------------
# Extract allergens
# --------------------------
ALLERGENS = [
    "milk", "egg", "soy", "peanut", "fish", "gluten",
    "sesame", "mustard", "celery", "lupin"
]

# will update the allergens extraction because the table needs to be interpreted as present or not
def extract_allergens(text):
   """"" found = []
    lower = text.lower()
    for a in ALLERGENS:
        if a in lower:
            found.append(a)
    return list(set(found))"""
   prompt = (f"You are a food allergen detection expert.Given the extracted text {text}, identify ALL allergens present an return only the allergen name found")
   response = client.chat.completions.create(
           model="gpt-5.1",
           messages=[{"role": "user","content": prompt}]
       )
   return response.choices[0].message.content



# --------------------------
# Extract nutrition valuesw
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
