import csv
import re
import unicodedata
from pathlib import Path

FOODS_FILE = Path("data/foods.csv")

MAX_CANDIDATES = 5

# Türkçe harf dönüşümleri
_TR_LOWER = str.maketrans({"İ": "i", "I": "ı"})   # Python'un "İ".lower() hatasını önler
_TR_FOLD = str.maketrans("çğıöşü", "cgiosu")      # noktasız yazımlarla da eşleşsin


def normalize_text(text):
    """Karşılaştırma için metni hazırlar.

    - Türkçe büyük/küçük harf kuralı (İ -> i, I -> ı)
    - noktalama temizlenir, boşluklar tekilleştirilir
    - ç ğ ı ö ş ü -> c g i o s u
    """
    text = unicodedata.normalize("NFC", text).translate(_TR_LOWER).lower()
    text = text.replace("\u0307", "")
    text = re.sub(r"[^\w\s]", " ", text)
    text = text.translate(_TR_FOLD)
    return " ".join(text.split())


# Tek başına yemeğin kimliğini belirtmeyen niteleyici kelimeler.
# Bunlar aday olmak için yetmez; sadece sıralamaya küçük katkı yapar.
WEAK_WORDS = {normalize_text(word) for word in [
    "ve", "ile", "et", "eti", "yemek", "yemeği", "geleneksel", "ev", "yapımı",
    "pişmiş", "haşlanmış", "ızgara", "fırında", "kızarmış", "közlenmiş",
    "kuru", "taze", "çiğ", "tam", "yağlı", "yağsız", "beyaz", "suda",
    "sütlü", "bitter",
]}


def _words_match(a, b):
    """İki kelime aynıysa veya biri (4+ harf) diğerinin başlangıcıysa eşleşir.

    Örnek: nohutlu ~ nohut, pilavı ~ pilav.
    """
    if a == b:
        return True

    short, long_ = sorted((a, b), key=len)
    return len(short) >= 4 and long_.startswith(short)


def load_foods():
    """foods.csv dosyasındaki besinleri yükler."""
    foods = []

    with open(FOODS_FILE, "r", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)

        for row in reader:
            foods.append({
                "name": row["name"],
                "kcal_per_100g": float(row["kcal_per_100g"]),
                "protein_g": float(row["protein_g"]),
                "carbs_g": float(row["carbs_g"]),
                "fat_g": float(row["fat_g"]),
                "source": row["source"]
            })

    return foods


def find_food(food_name, foods):
    """Yemek adını besin tablosunda arar. Sadece KESİN eşleşmeyi döndürür.

    Kesin eşleşme: normalize edilmiş kelimeler aynı (sıra önemsiz).
    Örn. "Haşlanmış yumurta" = "Yumurta haşlanmış".
    Benzer/kısmi eşleşmeler find_food_candidates ile aday olarak sunulur.
    """

    search_words = sorted(normalize_text(food_name).split())

    if not search_words:
        return None

    for food in foods:
        if sorted(normalize_text(food["name"]).split()) == search_words:
            return food

    return None

def find_food_candidates(food_name, foods):
    """Yemek adına göre olası besin kayıtlarını bulur.

    Aday olmak için sorgudaki en az bir "güçlü" kelimenin (WEAK_WORDS dışında)
    tablodaki adda geçmesi gerekir. En iyi MAX_CANDIDATES aday döner.
    """

    query_words = normalize_text(food_name).split()
    strong_words = [w for w in query_words if w not in WEAK_WORDS]
    weak_words = [w for w in query_words if w in WEAK_WORDS]

    scored = []

    for food in foods:
        food_words = normalize_text(food["name"]).split()

        matched_strong = {
            q for q in strong_words
            if any(_words_match(q, f) for f in food_words)
        }

        if not matched_strong:
            continue

        matched_weak = {
            q for q in weak_words
            if any(_words_match(q, f) for f in food_words)
        }

        candidate = {
            "food": food,
            "matched_words": matched_strong | matched_weak,
            "match_count": len(matched_strong)
        }

        sort_key = (
            -len(matched_strong),
            -len(matched_weak),
            len(food_words),
            food["name"]
        )

        scored.append((sort_key, candidate))

    scored.sort(key=lambda pair: pair[0])

    return [candidate for _, candidate in scored[:MAX_CANDIDATES]]

def match_food(food_name, foods):
    """
    Yemek adını besin tablosuyla eşleştirir.

    Sonuç:
    - exact: Kesin eşleşme
    - candidates: Olası adaylar
    - none: Hiç eşleşme yok
    """

    exact_match = find_food(food_name, foods)

    if exact_match:
        return {
            "status": "exact",
            "food": exact_match,
            "candidates": []
        }

    candidates = find_food_candidates(food_name, foods)

    if not candidates:
        return {
            "status": "none",
            "food": None,
            "candidates": []
        }

    return {
        "status": "candidates",
        "food": None,
        "candidates": candidates
    }

def calculate_nutrition(food, grams):
    """Gramaja göre besin değerlerini hesaplar."""

    multiplier = grams / 100

    return {
        "grams": grams,
        "kcal": round(food["kcal_per_100g"] * multiplier, 2),
        "protein_g": round(food["protein_g"] * multiplier, 2),
        "carbs_g": round(food["carbs_g"] * multiplier, 2),
        "fat_g": round(food["fat_g"] * multiplier, 2)
    }

def calculate_meal(detected_items, foods, corrections=None):
    """Tespit edilen yiyeceklerin besin değerlerini hesaplar.

    corrections:
        Modelin eşleştiremediği yiyecekler için kullanıcı seçimlerini içerir.
        Örnek:
        {
            "Haşlanmış tavuk eti": "Tavuk göğsü haşlanmış"
        }
    """

    if corrections is None:
        corrections = {}

    results = []

    total_kcal = 0
    total_protein = 0
    total_carbs = 0
    total_fat = 0

    for item in detected_items:

        match_result = match_food(item["name"], foods)

        # Kullanıcının daha önce yaptığı bir düzeltme varsa
        if item["name"] in corrections:

            selected_name = corrections[item["name"]]

            selected_food = find_food(
                selected_name,
                foods
            )

            if selected_food:
                match_result = {
                    "status": "exact",
                    "food": selected_food,
                    "candidates": []
                }

        if match_result["status"] != "exact":

            results.append({
                "name": item["name"],
                "grams": item["grams"],
                "confidence": item["confidence"],
                "status": match_result["status"],
                "food": None,
                "nutrition": None,
                "candidates": match_result["candidates"]
            })

            continue

        food = match_result["food"]

        nutrition = calculate_nutrition(
            food,
            item["grams"]
        )

        results.append({
            "name": item["name"],
            "grams": item["grams"],
            "confidence": item["confidence"],
            "status": "exact",
            "food": food,
            "nutrition": nutrition,
            "candidates": []
        })

        total_kcal += nutrition["kcal"]
        total_protein += nutrition["protein_g"]
        total_carbs += nutrition["carbs_g"]
        total_fat += nutrition["fat_g"]

    return {
        "items": results,
        "totals": {
            "kcal": round(total_kcal, 2),
            "protein_g": round(total_protein, 2),
            "carbs_g": round(total_carbs, 2),
            "fat_g": round(total_fat, 2)
        }
    }

if __name__ == "__main__":

    foods = load_foods()

    print(f"Besin tablosu yüklendi: {len(foods)} yiyecek")

    # Gemini'den geldiğini varsaydığımız veriler
    detected_items = [
        {
            "name": "Nohutlu pirinç pilavı",
            "grams": 220,
            "confidence": 0.95
        },
        {
            "name": "Haşlanmış tavuk eti",
            "grams": 50,
            "confidence": 0.90
        }
    ]

    total_kcal = 0
    total_protein = 0
    total_carbs = 0
    total_fat = 0

    print("\nBesin hesaplama sonucu:\n")

    for item in detected_items:

        food = find_food(item["name"], foods)

        if food is None:
            print(f"⚠️ Bulunamadı: {item['name']}")
            continue

        result = calculate_nutrition(food, item["grams"])

        print(f"Yiyecek: {item['name']}")
        print(f"Eşleşen kayıt: {food['name']}")
        print(f"Gram: {item['grams']} g")
        print(f"Kalori: {result['kcal']} kcal")
        print(f"Protein: {result['protein_g']} g")
        print(f"Karbonhidrat: {result['carbs_g']} g")
        print(f"Yağ: {result['fat_g']} g")
        print()

        total_kcal += result["kcal"]
        total_protein += result["protein_g"]
        total_carbs += result["carbs_g"]
        total_fat += result["fat_g"]

    print("------ TOPLAM ------")
    print(f"Kalori: {round(total_kcal, 2)} kcal")
    print(f"Protein: {round(total_protein, 2)} g")
    print(f"Karbonhidrat: {round(total_carbs, 2)} g")
    print(f"Yağ: {round(total_fat, 2)} g")