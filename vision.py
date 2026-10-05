"""Gemini Vision ile yemek fotoğrafı analizi.

Akış: image -> Gemini (veya Mock Mode) -> JSON -> Pydantic -> FoodAnalysis
"""

import json
import os
from pathlib import Path

from google.genai import types
from pydantic import ValidationError

from models import FoodAnalysis

DEFAULT_MODEL = "gemini-3.5-flash-lite"
MOCK_FILE = Path(__file__).parent / "fixtures" / "mock_analysis.json"
MAX_ATTEMPTS = 2  # ilk deneme + 1 retry

PROMPT = """
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

RETRY_HINT = "\n\nÖnceki cevabın geçersizdi. Yalnızca yukarıdaki JSON formatında cevap ver."


class VisionError(Exception):
    """Kullanıcıya olduğu gibi gösterilebilecek, anlaşılır analiz hatası."""


def _clean_json_text(text):
    """Gemini'nin cevabındaki olası ```json ... ``` işaretlerini temizler."""
    text = text.strip()

    text = text.removeprefix("```json")

    text = text.removesuffix("```")

    return text.strip()


def _parse_analysis(text):
    """Metni JSON'a çevirir ve Pydantic ile doğrular."""
    return FoodAnalysis.model_validate(json.loads(_clean_json_text(text)))


def _mock_analysis():
    """fixtures/mock_analysis.json dosyasından hazır analizi okur."""
    try:
        data = json.loads(MOCK_FILE.read_text(encoding="utf-8"))
        return FoodAnalysis.model_validate(data)
    except (OSError, json.JSONDecodeError, ValidationError) as e:
        raise VisionError(f"Mock dosyası okunamadı ({MOCK_FILE.name}): {e}") from e


def analyze_image(image, client=None, mock_mode=False):
    """Fotoğrafı analiz eder ve doğrulanmış FoodAnalysis döndürür.

    mock_mode=True ise Gemini çağrılmaz, hazır örnek kullanılır.
    Hata durumunda VisionError fırlatır.
    """
    if mock_mode:
        return _mock_analysis()

    if client is None:
        raise VisionError("Gemini istemcisi hazır değil. GEMINI_API_KEY tanımlı mı?")

    model = os.getenv("GEMINI_MODEL", DEFAULT_MODEL)

        # response_schema kullanılmıyor: google-genai 2.27.0, Pydantic'teki gt=0 kuralını
    # (exclusiveMinimum) şemaya çeviremiyor ve hata veriyor. JSON formatını
    # response_mime_type + PROMPT sağlar, doğrulamayı Pydantic yapar.
    config = types.GenerateContentConfig(
        response_mime_type="application/json",
    )

    last_problem = ""

    for attempt in range(1, MAX_ATTEMPTS + 1):
        prompt = PROMPT if attempt == 1 else PROMPT + RETRY_HINT

        try:
            response = client.models.generate_content(
                model=model,
                contents=[prompt, image],
                config=config,
            )
        except Exception as e:  # SDK hata türleri değişkenlik gösterir
            raise VisionError(f"Gemini API çağrısı başarısız oldu: {e}") from e

        text = (response.text or "").strip()

        if not text:
            last_problem = "Gemini boş cevap döndürdü."
            continue

        try:
            return _parse_analysis(text)
        except json.JSONDecodeError:
            last_problem = "Gemini geçerli JSON döndürmedi."
        except ValidationError:
            last_problem = "Gemini cevabı beklenen formata uymuyor (ör. gramaj veya güven değeri geçersiz)."

    raise VisionError(
        f"{last_problem} {MAX_ATTEMPTS} denemeden sonra analiz tamamlanamadı. Lütfen tekrar dene."
    )