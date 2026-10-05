import json
import os

from dotenv import load_dotenv
from google import genai
from PIL import Image

from models import FoodAnalysis

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

print("API key bulundu:", bool(api_key))

if not api_key:
    raise ValueError("GEMINI_API_KEY bulunamadı!")


client = genai.Client(api_key=api_key)

image = Image.open("test_images/images.jpg")

prompt = """
Bu fotoğrafı analiz et.

Fotoğrafta görünen yiyecekleri tespit et.
Her yiyecek için:

- name: yiyeceğin adı
- grams: tahmini gramaj
- confidence: 0 ile 1 arasında güven skoru

Sadece JSON formatında cevap ver:

{
  "items": [
    {
      "name": "yiyecek adı",
      "grams": 100,
      "confidence": 0.85
    }
  ],
  "notes": "Varsa kısa not"
}

Kalori veya besin değerlerini hesaplama.
Tahmin edemediğin bir yiyeceği uydurma.
"""


response = client.models.generate_content(
    model="gemini-3.5-flash-lite",
    contents=[prompt, image]
)

print("\nGemini ham cevabı:\n")
print(response.text)


# Markdown kod bloğu varsa temizle
cleaned_response = response.text.strip()

cleaned_response = cleaned_response.removeprefix("```json")

cleaned_response = cleaned_response.removesuffix("```")

cleaned_response = cleaned_response.strip()


# JSON'a çevir
try:
    data = json.loads(cleaned_response)
except json.JSONDecodeError:
    print("\nHATA: Gemini geçerli JSON döndürmedi.")
    raise


# Pydantic ile doğrula
try:
    analysis = FoodAnalysis.model_validate(data)
except Exception as e:
    print("\nHATA: Gemini cevabı beklenen formata uymuyor.")
    print(e)
    raise


print("\nPydantic doğrulaması başarılı!\n")

for item in analysis.items:
    print(
        f"- {item.name} | "
        f"{item.grams} g | "
        f"confidence: {item.confidence}"
    )

print(f"\nNot: {analysis.notes}")

from nutrition import calculate_meal, load_foods

foods = load_foods()

detected_items = [
    {
        "name": item.name,
        "grams": item.grams,
        "confidence": item.confidence
    }
    for item in analysis.items
]

meal_result = calculate_meal(
    detected_items,
    foods
)

print("\nBesin hesaplama sonucu:\n")
print(meal_result)