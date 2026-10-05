from nutrition import (
    calculate_meal,
    calculate_nutrition,
    find_food,
    find_food_candidates,
    load_foods,
    match_food,
)

foods = load_foods()


def test_load_foods_has_at_least_50_foods():
    assert len(foods) >= 50


def test_find_food_exact_match():
    food = find_food("Pirinç pilavı", foods)

    assert food is not None
    assert food["name"] == "Pirinç pilavı"


def test_find_food_unknown_returns_none():
    food = find_food("Tamamen olmayan yemek", foods)

    assert food is None


def test_find_food_candidates_for_chicken():
    candidates = find_food_candidates("Haşlanmış tavuk eti", foods)

    assert candidates

    candidate_names = [
        candidate["food"]["name"]
        for candidate in candidates
    ]

    assert "Tavuk göğsü haşlanmış" in candidate_names


def test_match_food_exact():
    result = match_food("Pirinç pilavı", foods)

    assert result["status"] == "exact"
    assert result["food"]["name"] == "Pirinç pilavı"


def test_match_food_candidates():
    result = match_food("Haşlanmış tavuk eti", foods)

    assert result["status"] == "candidates"
    assert result["candidates"]


def test_match_food_none():
    result = match_food("Uzay yemeği 999", foods)

    assert result["status"] == "none"
    assert result["candidates"] == []


def test_calculate_nutrition():
    food = find_food("Pirinç pilavı", foods)

    result = calculate_nutrition(food, 220)

    assert result["kcal"] == 286
    assert result["protein_g"] == 5.94
    assert result["carbs_g"] == 62.04
    assert result["fat_g"] == 0.66


def test_calculate_meal_with_exact_matches():
    items = [
        {
            "name": "Pirinç pilavı",
            "grams": 220,
            "confidence": 0.95,
        },
        {
            "name": "Tavuk göğsü haşlanmış",
            "grams": 100,
            "confidence": 0.90,
        },
    ]

    result = calculate_meal(items, foods)

    assert result["totals"]["kcal"] > 0
    assert result["totals"]["protein_g"] > 0
    assert result["totals"]["carbs_g"] > 0
    assert result["totals"]["fat_g"] >= 0


def test_calculate_meal_unknown_food_is_not_added():
    items = [
        {
            "name": "Uzay yemeği 999",
            "grams": 100,
            "confidence": 0.50,
        }
    ]

    result = calculate_meal(items, foods)

    assert result["totals"]["kcal"] == 0
    assert result["totals"]["protein_g"] == 0
    assert result["totals"]["carbs_g"] == 0
    assert result["totals"]["fat_g"] == 0

    assert result["items"][0]["status"] == "none"
    assert result["items"][0]["nutrition"] is None


def test_calculate_meal_correction():
    items = [
        {
            "name": "Haşlanmış tavuk eti",
            "grams": 100,
            "confidence": 0.90,
        }
    ]

    corrections = {
        "Haşlanmış tavuk eti": "Tavuk göğsü haşlanmış"
    }

    result = calculate_meal(
        items,
        foods,
        corrections=corrections,
    )

    assert result["totals"]["kcal"] > 0
    assert result["items"][0]["status"] == "exact"
    assert result["items"][0]["food"]["name"] == "Tavuk göğsü haşlanmış"