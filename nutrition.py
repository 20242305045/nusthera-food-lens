import csv
from pathlib import Path


FOODS_FILE = Path("data/foods.csv")


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
    """Yemek adını besin tablosunda arar."""

    search_name = food_name.lower().strip()

    # Önce birebir eşleşme
    for food in foods:
        if food["name"].lower() == search_name:
            return food

    # Daha sonra isim içinde eşleşme
    for food in foods:
        table_name = food["name"].lower()

        if search_name in table_name or table_name in search_name:
            return food

    return None

def find_food_candidates(food_name, foods):
    """Yemek adına göre olası besin kayıtlarını bulur."""

    search_words = set(food_name.lower().split())

    # Çok genel kelimeleri çıkarıyoruz.
    stop_words = {
        "ve",
        "ile",
        "eti",
        "et",
        "yemeği",
        "yemek",
        "pişmiş",
        "geleneksel"
    }

    search_words = search_words - stop_words

    candidates = []

    for food in foods:
        food_words = set(food["name"].lower().split())

        common_words = search_words.intersection(food_words)

        if common_words:
            candidates.append({
                "food": food,
                "matched_words": common_words,
                "match_count": len(common_words)
            })

    candidates.sort(
        key=lambda x: x["match_count"],
        reverse=True
    )

    return candidates

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