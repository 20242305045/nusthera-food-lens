# Food Lens — Design

## 1. Architecture

Food Lens separates AI vision, nutrition calculation, user correction, persistence, and evaluation.

```text
User
  ↓
app.py / Streamlit UI
  ↓
vision.py
  ├─ Mock → fixtures/mock_analysis.json
  └─ Live → Gemini Vision API
  ↓
models.py / Pydantic validation
  ↓
nutrition.py
  ├─ Turkish text normalization
  ├─ food matching / candidate selection
  └─ deterministic nutrition calculation
  ↓
data/foods.csv
  ↓
User review and correction
  ↓
database.py
  ↓
SQLite / daily totals

Evaluation:
test images + labels → eval/run_eval.py → predictions + metrics
```

### Main responsibilities

- **`app.py`**: Streamlit UI and application flow. Handles image upload, mode selection, displaying predictions, user corrections, saving meals, and daily totals.
- **`vision.py`**: AI boundary. Sends images to Gemini in live mode, loads recorded responses in mock mode, parses JSON, validates it, and handles retry/API errors.
- **`models.py`**: Pydantic data contract for `FoodAnalysis` and `FoodItem`. Invalid model output is rejected before entering the application logic.
- **`nutrition.py`**: Matches detected foods to the reference table and calculates nutrition values. Gemini is not used to calculate nutrition.
- **`data/foods.csv`**: Reference nutrition data per 100 g.
- **`database.py`**: Stores confirmed meals locally in SQLite and supports daily totals.
- **`fixtures/`**: Recorded model responses for API-independent Mock Mode.
- **`eval/`**: Separate evaluation pipeline for recognition and calorie error.

## 2. Data Flow and Nutrition

The vision model is responsible only for identifying visible foods, estimating grams, and returning confidence.

The application validates the response with Pydantic. Food names are then normalized and matched against the local nutrition table. Matching uses exact matches first and candidate/fuzzy matching when necessary. If no reliable match exists, the user can select another food or leave the item unmatched.

Nutrition is calculated deterministically by application code:

```text
nutrient = grams × value_per_100g / 100
```

The model's own nutrition estimates are never trusted or used for the final calculation.

Before saving, the user can correct the food selection and grams. Nutrition values are recalculated from the corrected values.

## 3. Mock Mode and Error Handling

Mock Mode loads a recorded response from `fixtures/` instead of calling Gemini. The response follows the same Pydantic validation and nutrition pipeline as live mode, so Mock Mode tests the real application flow without an API key.

Invalid or empty AI responses are not passed directly to the UI/business logic. The vision layer attempts a limited retry and then returns a user-friendly error.

API failures, invalid model output, missing nutrition matches, and other expected failures are handled without exposing internal errors unnecessarily.

## 4. Privacy and Security

The application does not claim to provide medical, diagnostic, or treatment advice. Food recognition and calorie estimates are approximate and can be wrong.

Uploaded food images may be sent to the configured Gemini Vision API in live mode for analysis. The prototype does not intentionally collect user identity information or credentials. The Gemini API key is stored in `.env` and `.env` is excluded from Git.

Confirmed meals are stored locally in SQLite for the prototype. The database is not intended to be a production-grade health-data storage system.

Allergen information is not independently verified by Food Lens. Users should not rely on the prototype to determine whether food is safe for an allergy or medical condition.

Only photos that the user has permission to process should be used, and photos containing unnecessary personal or identifying information should be avoided.

## 5. Design Decisions and Limitations

The prototype deliberately keeps the architecture simple:

- Streamlit provides a fast UI.
- Gemini handles vision instead of custom computer-vision training.
- Pydantic creates a clear boundary between model output and application logic.
- A local CSV keeps nutrition calculation deterministic and inspectable.
- SQLite provides simple persistence without requiring a backend service.
- User correction provides a human-in-the-loop fallback when vision or food matching is uncertain.

Important limitations include imperfect food recognition, approximate gram estimation, limited nutrition coverage, ambiguous food names, and dependence on the external vision model in live mode.

## 6. Future Medication-App Scenario

A medication application would require a substantially stricter architecture because an incorrect food estimate and an incorrect medication instruction have very different safety consequences.

The system should **not** diagnose conditions, prescribe medication, change dosage, or make treatment decisions from an image or AI-generated interpretation. Medication identity, dosage, interactions, contraindications, and patient-specific decisions would require authoritative sources and appropriate human/clinical oversight.

Before release, such a system would need, at minimum, validated medication data sources, deterministic safety rules, strong authentication and access controls, audit logging, privacy/security controls appropriate for sensitive health data, comprehensive testing, monitoring, and qualified medical/regulatory review.

The Food Lens prototype therefore treats AI as an estimation component rather than a source of authoritative medical decisions.