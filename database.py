import sqlite3
from datetime import datetime


DB_FILE = "food_lens.db"


def init_database():
    """Veritabanını ve meals tablosunu oluşturur."""

    connection = sqlite3.connect(DB_FILE)

    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS meals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            kcal REAL NOT NULL,
            protein_g REAL NOT NULL,
            carbs_g REAL NOT NULL,
            fat_g REAL NOT NULL
        )
    """)

    connection.commit()
    connection.close()


def save_meal(meal_result):
    """Hesaplanan öğünü veritabanına kaydeder."""

    totals = meal_result["totals"]

    connection = sqlite3.connect(DB_FILE)

    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO meals (
            created_at,
            kcal,
            protein_g,
            carbs_g,
            fat_g
        )
        VALUES (?, ?, ?, ?, ?)
    """, (
        datetime.now().isoformat(),
        totals["kcal"],
        totals["protein_g"],
        totals["carbs_g"],
        totals["fat_g"]
    ))

    connection.commit()
    connection.close()

def get_daily_total():
    """Bugün kaydedilen öğünlerin toplam besin değerlerini getirir."""

    today = datetime.now().strftime("%Y-%m-%d")

    connection = sqlite3.connect(DB_FILE)

    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            COALESCE(SUM(kcal), 0),
            COALESCE(SUM(protein_g), 0),
            COALESCE(SUM(carbs_g), 0),
            COALESCE(SUM(fat_g), 0)
        FROM meals
        WHERE created_at LIKE ?
    """, (today + "%",))

    result = cursor.fetchone()

    connection.close()

    return {
        "kcal": round(result[0], 2),
        "protein_g": round(result[1], 2),
        "carbs_g": round(result[2], 2),
        "fat_g": round(result[3], 2)
    }
