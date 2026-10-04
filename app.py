import streamlit as st
import os

from dotenv import load_dotenv
from google import genai
from PIL import Image

from nutrition import load_foods, calculate_meal, match_food
from database import init_database, save_meal, get_daily_total
from vision import analyze_image, VisionError

init_database()


load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

mock_mode = os.getenv("MOCK_MODE", "false").lower() == "true"

if not api_key and not mock_mode:
    st.error("GEMINI_API_KEY bulunamadı.")
    st.stop()

client = genai.Client(api_key=api_key) if api_key else None

foods = load_foods()


# Session state
if "analysis" not in st.session_state:
    st.session_state.analysis = None


# Sayfa ayarları
st.set_page_config(
    page_title="Food Lens",
    page_icon="🍽️",
    layout="centered"
)


st.title("🍽️ Food Lens")
st.write("Fotoğrafını yükle, yemeğini analiz edelim.")


uploaded_file = st.file_uploader(
    "Yemek fotoğrafı yükle",
    type=["jpg", "jpeg", "png"]
)


if uploaded_file is not None:

    st.image(
        uploaded_file,
        caption="Yüklenen fotoğraf",
        use_container_width=True
    )

    st.success("Fotoğraf başarıyla yüklendi!")


    if st.button("🔍 Yemeği Analiz Et"):

        with st.spinner("Yemek analiz ediliyor..."):
         
           with st.spinner("Yemek analiz ediliyor..."):

               try:
                  image = None if mock_mode else Image.open(uploaded_file)

                  st.session_state.analysis = analyze_image(
                      image,
                      client=client,
                      mock_mode=mock_mode
                   )

               except VisionError as e:
                   st.error(str(e))

# --------------------------------------------------
# ANALİZ SONUCU
# --------------------------------------------------

if st.session_state.analysis is not None:

    st.success("Yemek analizi tamamlandı!")


    analysis = st.session_state.analysis


    st.subheader("Tespit edilen yiyecekler")


    for item in analysis.items:

        st.write(
            f"**{item.name}** — "
            f"{item.grams} g — "
            f"Güven: {item.confidence:.2f}"
        )


    if analysis.notes:

        st.info(analysis.notes)


    # Gemini sonucunu hesaplama fonksiyonunun
    # beklediği formata çevir

    detected_items = [

        {
            "name": item.name,
            "grams": item.grams,
            "confidence": item.confidence
        }

        for item in analysis.items
    ]

    # Kullanıcının gramaj düzeltmelerini al
    for item in detected_items:

        new_grams = st.number_input(
            f"{item['name']} gramajı:",
            min_value=1.0,
            value=float(item["grams"]),
            step=1.0,
            key=f"grams_{item['name']}"
        )

        item["grams"] = new_grams


    # Kullanıcı düzeltmelerini tutacak sözlük
    corrections = {}


    # Eşleşmeyen yiyecekler için kullanıcıdan seçim al
    for item in detected_items:

        match_result = match_food(
            item["name"],
            foods
        )

        if match_result["status"] == "candidates":

            candidate_names = [
                candidate["food"]["name"]
                for candidate in match_result["candidates"]
            ]

            selected_food = st.selectbox(
                f"{item['name']} için besin kaydı seç:",
                candidate_names,
                key=f"correction_{item['name']}"
            )

            corrections[item["name"]] = selected_food


    # Kullanıcı seçimleriyle birlikte besin değerlerini hesapla
    meal_result = calculate_meal(
        detected_items,
        foods,
        corrections
    )

   
    st.subheader("🥗 Besin Değerleri")


    for item in meal_result["items"]:

        st.write(f"### {item['name']}")


        if item["status"] == "exact":

            nutrition = item["nutrition"]


            st.write(
                f"**Gram:** {nutrition['grams']} g"
            )

            st.write(
                f"**Kalori:** {nutrition['kcal']} kcal"
            )

            st.write(
                f"**Protein:** {nutrition['protein_g']} g"
            )

            st.write(
                f"**Karbonhidrat:** {nutrition['carbs_g']} g"
            )

            st.write(
                f"**Yağ:** {nutrition['fat_g']} g"
            )


        else:

            st.warning(
                f"{item['name']} için otomatik eşleştirme bulunamadı."
            )


    st.subheader("📊 Toplam")


    totals = meal_result["totals"]


    st.write(
        f"**Kalori:** {totals['kcal']} kcal"
    )

    st.write(
        f"**Protein:** {totals['protein_g']} g"
    )

    st.write(
        f"**Karbonhidrat:** {totals['carbs_g']} g"
    )

    st.write(
        f"**Yağ:** {totals['fat_g']} g"
    )
            # Öğünü kaydet
    if st.button("💾 Yemeği Kaydet"):
        save_meal(meal_result)
        st.success("Yemek başarıyla kaydedildi! ✅")

    # Günlük toplam
    st.subheader("📅 Bugünün Toplamı")

    daily_total = get_daily_total()

    st.write(f"**Kalori:** {daily_total['kcal']} kcal")
    st.write(f"**Protein:** {daily_total['protein_g']} g")
    st.write(f"**Karbonhidrat:** {daily_total['carbs_g']} g")
    st.write(f"**Yağ:** {daily_total['fat_g']} g")