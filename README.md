# SignMark

SignMark is a web application for practising and exploring American Sign Language (ASL). It combines a Flask backend, browser-based pages, and trained image-classification models.

## Features

- **Sign Studio:** Upload a sign image for automatic prediction, or use live recognition with a selected category.
- **Dictionary:** Browse signs supported by the available models. Dictionary media is served from `static/signs/`.
- **Quiz:** Practise using six quiz modes and view saved, per-user progress.
- **Insights:** View available model evaluation details and report charts.
- **Accounts:** Register and sign in using a SQLite user store and Flask sessions.
- **Text to speech:** Uses the browser’s speech synthesis feature.

Recognition results depend on the classes in the trained models. ASL signs that require movement may not be reliably recognized from a single still image.

## Technologies

- Python and Flask
- SQLite
- TensorFlow / Keras
- OpenCV, NumPy and Pillow
- scikit-learn and Matplotlib for model and evaluation tools
- HTML, CSS and JavaScript

## Project structure

```text
SignMark/
├── app.py
├── requirements.txt
├── src/
│   ├── api/                 # Flask routes for pages, accounts, prediction and content
│   ├── app_factory.py       # Application setup and route registration
│   ├── auth_db.py           # SQLite account and quiz-progress storage
│   ├── model_service.py     # Loads models and predicts signs
│   └── ...                  # Dataset, preprocessing, training and evaluation tools
├── templates/               # Jinja/HTML pages
├── static/                  # CSS, JavaScript, logos and browser assets
│   └── signs/               # Dictionary sign images and videos
├── models/                  # Trained models and their metadata
├── data/                    # Local database and dataset files
├── reports/                 # Evaluation results and charts
└── tests/                   # Automated tests
```

## Run locally

Python 3.11 is the version used for the current project environment.

### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python app.py
```

Then open [http://127.0.0.1:5000](http://127.0.0.1:5000).

The server starts with login required. The SQLite database is initialized under `data/` when the app starts. The trained model files and matching metadata must be present in `models/` for recognition to work.

## Main pages

- `/` — landing page
- `/auth` — sign in and account creation
- `/home` — dashboard
- `/studio` — sign recognition
- `/dictionary` — sign dictionary
- `/quiz` — quiz and progress
- `/insights` — model insights
- `/about` — project information

## Recognition flow

The browser sends an uploaded image or camera frame to a Flask API route. The backend decodes and prepares the image, then `src/model_service.py` selects the requested trained model and returns its prediction and confidence. The page displays the result.

The available prediction tasks are alphabet, numbers and phrases. Upload recognition can select a model automatically; live recognition uses the chosen category.

## Run tests

```powershell
python -m unittest tests.test_api tests.test_chunk2
```

## Model and dataset files

The training and evaluation scripts are in `src/`. Running the web app does not require retraining if the trained models are already present.

Check that the required model files and metadata are available under `models/`. The project’s `.gitignore` excludes model files with extensions such as `.keras`; make sure the models are made available separately or intentionally included when setting up a fresh clone.

Dictionary sign media belongs in `static/signs/`. The app supports common image formats and videos when a matching media file is present.
