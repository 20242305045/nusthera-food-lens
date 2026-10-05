import csv
import json
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from nutrition import find_food, load_foods

BASE_DIR = Path(__file__).resolve().parent.parent
LABELS_FILE = BASE_DIR / "eval" / "labels.csv"
RESULTS_FILE = BASE_DIR / "eval" / "predictions.json"


# Calorie error hesabına dahil edilecek 10 örnek.
# 5 karmaşık yemek bilinçli olarak dışarıda bırakılıyor.
CALORIE_IMAGES = {
    "cheese-burger-7323672_1280.jpg",
    "depositphotos_384578202-stock-photo-traditional-turkish-food-menemen-made.jpg",
    "fırındatavukimages.jpg",
    "images (2).jpg",
    "images (4).jpg",
    "images (5).jpg",
    "images (7).jpg",
    "images (8).jpg",
    "images - Kopya.jpg",
    "tantuni.jpg",
}


def normalize(text):
    text = unicodedata.normalize("NFKD", text)

    text = "".join(
        char
        for char in text
        if not unicodedata.combining(char)
    )

    return " ".join(
        text.lower().strip().split()
    )


def load_labels():
    with open(
        LABELS_FILE,
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        return list(csv.DictReader(file))


def load_predictions():
    with open(
        RESULTS_FILE,
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def get_predicted_items(result):
    return result.get("items", [])


def matches_expected(expected, predicted_items):
    expected = normalize(expected)

    aliases = {
        "hamburger": [
            "hamburger",
            "hamburger ekmegi",
            "burger",
        ],
        "menemen": [
            "menemen",
        ],
        "fırında tavuk": [
            "fırında tavuk",
            "bütün fırın tavuk",
        ],
        "içli köfte": [
            "içli köfte",
        ],
        "köfte": [
            "köfte",
            "ızgara köfte",
            "dana köfte",
        ],
        "sarma": [
            "sarma",
            "yaprak sarma",
        ],
        "kebap": [
            "kebap",
            "adana kebap",
            "şiş kebap",
        ],
        "pizza": [
            "pizza",
        ],
        "mercimek çorbası": [
            "mercimek çorbası",
        ],
        "haşlanmış yumurta": [
            "haşlanmış yumurta",
            "yumurta haşlanmış",
        ],
        "et sote": [
            "et sote",
        ],
        "tavuklu pilav": [
            "tavuklu pilav",
            "tavuklu ve nohutlu pirinç pilavı",
        ],
        "çiğ köfte": [
            "çiğ köfte",
        ],
        "karnıyarık": [
            "karnıyarık",
        ],
        "tantuni": [
            "tantuni",
        ],
    }

    possible_names = aliases.get(expected, [expected])

    for item in predicted_items:
        predicted = normalize(item["name"])

        for possible in possible_names:
            possible = normalize(possible)

            # Tam eşleşme
            if predicted == possible:
                return True

            # Örneğin:
            # beklenen: köfte
            # model:    ızgara köfte
            if expected == "kofte" and "kofte" in predicted:
                return True

    return False


def find_food_for_eval(name, foods):
    """
    Evaluation sırasında mevcut nutrition matching
    fonksiyonunu kullanır.
    """

    food = find_food(
        name,
        foods,
    )

    if food:
        return food

    # Gemini'nin bazı yaygın çıktı isimlerini
    # mevcut nutrition tablosundaki karşılıklarına
    # güvenli şekilde yönlendiriyoruz.

    aliases = {
        "hamburger ekmeği": "Ekmek beyaz",
        "dana köfte": "Köfte",
        "ızgara köfte": "Köfte",
        "ızgara domates": "Domates",
        "közlenmiş domates": "Domates",
        "közlenmiş biber": "Biber Çarliston tipi",
        "ızgara biber": "Biber Çarliston tipi",
        "kırmızı biber": "Biber Çarliston tipi",
        "yeşil biber": "Biber Çarliston tipi",
        "maydanoz": "Maydanoz",
        "domates": "Domates",
        "fırın patates": "Patates haşlanmış",
        "haşlanmış yumurta": "Yumurta haşlanmış",
        "yumurta": "Yumurta haşlanmış",
        "pizza": "Pizza",
        "menemen": "Menemen",
        "et sote": "Et sote",
        "kavurma": "Dana eti pişmiş",
    }

    normalized_name = normalize(name)

    for alias, target in aliases.items():
        if normalized_name == normalize(alias):
            return find_food(
                target,
                foods,
            )

    return None


def calculate_predicted_kcal(predicted_items, foods):
    total_kcal = 0.0
    matched_items = []
    unmatched_items = []

    for item in predicted_items:
        name = item["name"]
        grams = float(item["grams"])

        food = find_food_for_eval(
            name,
            foods,
        )

        if food is None:
            unmatched_items.append(name)
            continue

        kcal = (
            food["kcal_per_100g"]
            * grams
            / 100
        )

        total_kcal += kcal

        matched_items.append({
            "name": name,
            "matched_food": food["name"],
            "grams": grams,
            "kcal": kcal,
        })

    return (
        total_kcal,
        matched_items,
        unmatched_items,
    )


def main():
    labels = load_labels()
    predictions = load_predictions()
    foods = load_foods()

    predictions_by_image = {
        result["image"]: result
        for result in predictions
    }

    recognition_correct = 0
    recognition_total = 0

    calorie_results = []

    print("=" * 60)
    print("FOOD LENS FINAL EVALUATION")
    print("=" * 60)

    # ---------------------------------------------------------
    # RECOGNITION
    # ---------------------------------------------------------

    print("\n--- RECOGNITION ---")

    for row in labels:
        image = row["image"]

        expected_items = [
            item.strip()
            for item in row["items"].split(";")
            if item.strip()
        ]

        result = predictions_by_image.get(
            image,
            {},
        )

        predicted_items = get_predicted_items(
            result
        )

        recognition_total += len(
            expected_items
        )

        correct = sum(
            1
            for expected in expected_items
            if matches_expected(
                expected,
                predicted_items,
            )
        )

        recognition_correct += correct

        print(
            f"{image}: "
            f"{correct}/{len(expected_items)}"
        )

    recognition_rate = (
        recognition_correct
        / recognition_total
        * 100
    )

    print(
        f"\nRecognition rate: "
        f"{recognition_rate:.1f}% "
        f"({recognition_correct}/{recognition_total})"
    )

    # ---------------------------------------------------------
    # CALORIE ERROR
    # ---------------------------------------------------------

    print("\n--- CALORIE ERROR ---")

    for row in labels:
        image = row["image"]

        if image not in CALORIE_IMAGES:
            continue

        true_kcal_text = row["true_kcal"].strip()

        if not true_kcal_text:
            continue

        true_kcal = float(
            true_kcal_text
        )

        result = predictions_by_image.get(
            image,
            {},
        )

        predicted_items = get_predicted_items(
            result
        )

        predicted_kcal, matched_items, unmatched_items = (
            calculate_predicted_kcal(
                predicted_items,
                foods,
            )
        )

        if predicted_kcal <= 0:
            print(
                f"{image}: "
                "calorie hesaplanamadı"
            )
            continue

        error_percent = (
            abs(
                predicted_kcal
                - true_kcal
            )
            / true_kcal
            * 100
        )

        calorie_results.append({
            "image": image,
            "true_kcal": true_kcal,
            "predicted_kcal": predicted_kcal,
            "error_percent": error_percent,
            "matched_items": matched_items,
            "unmatched_items": unmatched_items,
        })

        print(
            f"{image}"
        )
        print(
            f"  True kcal:      {true_kcal:.1f}"
        )
        print(
            f"  Predicted kcal: {predicted_kcal:.1f}"
        )
        print(
            f"  Error:          {error_percent:.1f}%"
        )

        if unmatched_items:
            print(
                "  Eşleşmeyenler: "
                + ", ".join(unmatched_items)
            )

    # ---------------------------------------------------------
    # SUMMARY
    # ---------------------------------------------------------

    print("\n" + "=" * 60)
    print("FINAL RESULTS")
    print("=" * 60)

    print(
        f"Recognition rate: "
        f"{recognition_rate:.1f}% "
        f"({recognition_correct}/{recognition_total})"
    )

    if calorie_results:
        average_error = sum(
            item["error_percent"]
            for item in calorie_results
        ) / len(calorie_results)

        print(
            f"Calorie error: "
            f"{average_error:.1f}% "
            f"({len(calorie_results)} images)"
        )

        print("\nWorst 3 photos:")

        worst_three = sorted(
            calorie_results,
            key=lambda item: item["error_percent"],
            reverse=True,
        )[:3]

        for index, item in enumerate(
            worst_three,
            start=1,
        ):
            print(
                f"{index}. "
                f"{item['image']} — "
                f"{item['error_percent']:.1f}%"
            )

    else:
        print(
            "Calorie error: "
            "hesaplanamadı"
        )

    print("=" * 60)


if __name__ == "__main__":
    main()