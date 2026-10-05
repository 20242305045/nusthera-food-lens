# Nusthera Food Lens

A Python + Streamlit prototype that analyzes food photos with Gemini Vision, estimates food items and grams, calculates nutrition from a local reference database, lets the user correct results, and stores confirmed meals.

## Features

- Food photo upload through a Streamlit UI
- Gemini Vision food detection
- Structured Pydantic validation
- Retry and invalid-response handling
- Mock Mode without an API key
- Local nutrition database with 50+ foods
- Deterministic calorie and macro calculation
- User correction before saving
- SQLite meal persistence
- Daily nutrition totals
- 15-image evaluation dataset
- Recognition and calorie-error metrics
- AI usage and design documentation

## Architecture

User
  |
  v
app.py
  |
  v
vision.py
  |
  +--> Mock Mode --> fixtures/mock_analysis.json
  |
  +--> Live Mode --> Gemini Vision
  |
  v
models.py
  |
  v
nutrition.py
  |
  v
data/foods.csv
  |
  v
User review / correction
  |
  v
database.py
  |
  v
SQLite
  |
  v
Daily totals

## Project Structure

nusthera-food-lens/
├── app.py
├── vision.py
├── models.py
├── nutrition.py
├── database.py
├── test_gemini.py
├── requirements.txt
├── .env.example
├── README.md
├── DESIGN.md
├── AI_USAGE.md
├── ai-history/
├── data/
│   └── foods.csv
├── fixtures/
│   └── mock_analysis.json
├── eval/
│   ├── images/
│   ├── labels.csv
│   ├── predictions.json
│   └── run_eval.py
├── tests/
│   ├── test_nutrition.py
│   └── test_vision.py
├── pytest.ini
├── .github/
│   └── workflows/
│       └── tests.yml
└── test_images/

## Setup

### Requirements

- Python 3.13
- Google Gemini API key for Live Mode

Install dependencies:

pip install -r requirements.txt

Create the environment file:

Copy-Item .env.example .env

Then add your Gemini API key to .env:

GEMINI_API_KEY=your_api_key_here
MOCK_MODE=false
GEMINI_MODEL=gemini-3.5-flash-lite

## Running the Application

Start Streamlit:

streamlit run app.py

The application is available at:

http://localhost:8501

The application mode is controlled through environment variables. The user uploads a food image from the Streamlit interface, while Mock Mode or Live Mode is selected through .env.

## Mock Mode

Mock Mode runs without an API key.

Set:

MOCK_MODE=true

The application loads the recorded response from:

fixtures/mock_analysis.json

The same validation, nutrition matching, correction, database, and daily-total pipeline is then used.

## Live Mode

Live Mode sends the uploaded image to Gemini Vision.

The model is responsible only for:

- identifying visible foods
- estimating grams
- assigning confidence
- returning structured JSON

The model does not calculate calories or macronutrients.

Pydantic validates the returned structure. Invalid or empty responses are retried once before showing a user-friendly error.

## Nutrition Calculation

Nutrition values come from:

data/foods.csv

The database contains more than 50 food records.

For each matched food, nutrition is calculated by application code:

grams × value_per_100g / 100

Gemini nutrition values are never trusted or used for the calculation.

If a food cannot be matched safely, the application can request user correction instead of silently assigning an unrelated food.

## User Correction

Before saving a meal, the user can:

- change the detected food
- change the estimated grams
- review the calculated nutrition

Nutrition is recalculated after corrections.

Only the reviewed result is saved.

## Evaluation

The evaluation dataset contains 15 labelled food images.

Run:

python eval/run_eval.py

The evaluation uses:

eval/labels.csv
eval/predictions.json

Recognition is measured as:

correctly recognized labelled foods / total labelled foods

Current result:

Recognition: 93.3% (14/15 labelled food items)

The recognition failure was:

tantuni.jpg

The model produced a different sandwich/kavurma-style composition instead of correctly identifying tantuni.

### Calorie Error

The current average calorie error is:

130.8%

This is calculated over 9 images with usable predicted calorie values.

The three worst examples are:

1. fırındatavukimages.jpg — 755.4%
2. images (5).jpg — 191.7%
3. images (7).jpg — 151.2%

The largest error comes from gram estimation. For example, the whole roasted chicken image was estimated at approximately 1200 g while the reference value used approximately 150 g edible cooked chicken.

## Testing

Automated tests are located in the `tests/` directory.

Run the full test suite:

python -m pytest -v

The project currently contains 15 automated tests covering nutrition matching, nutrition calculations, food corrections, and Gemini vision error handling.

### Continuous Integration

GitHub Actions runs automatically on every push and pull request.

The CI pipeline:

- installs the project dependencies
- runs Ruff linting
- runs all 15 automated tests

A successful CI run confirms that the code passes both linting and automated tests.

Linting:

ruff check .

Evaluation:

python eval/run_eval.py

Mock Mode can be used to test the application without an API key.

## Security and Privacy

This prototype does not implement authentication or production-level security.

Important considerations:

- API keys must stay in .env
- .env must not be committed
- SQLite database files should not be committed
- Uploaded food images may be sent to Gemini in Live Mode
- Images should not contain faces or unnecessary personal information
- Only images the user has the right to use should be included
- Food recognition and nutrition estimates are approximate
- Allergen information is not independently verified
- The application must not be presented as professional medical or dietary advice

## Known Limitations

- Food recognition can fail for visually similar or complex dishes.
- Portion-size estimation from a single image is approximate.
- Calorie error can become very large when the estimated grams are inaccurate.
- The nutrition database is limited to the included reference foods.
- Some Turkish dishes require better ingredient-level matching.
- No production authentication or deployment is implemented.
- The evaluation dataset is small and should not be treated as a clinical benchmark.

## AI-Assisted Development

AI tools were used during development for architecture discussions, implementation assistance, debugging, evaluation improvements, and documentation.

Important AI decisions and prompts are documented in:

AI_USAGE.md
ai-history/

The architecture and security/privacy decisions are documented in:

DESIGN.md

## Conclusion

Food Lens is intentionally implemented as a small, explainable prototype.

The central design principle is:

AI predicts what is visible; application code validates, matches, calculates, stores, and evaluates the result.
