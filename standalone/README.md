# SurveyGPT

A Q&A / problem-solving assistant for undergraduate **Surveying** (Civil Engineering):
chain & tape, compass surveying, levelling, theodolite & traverse computation,
tacheometry, curves, and area computation. Supports uploading a photo of a
problem (OCR) and generating quick charts.

## 1. Requirements

- Python 3.10+
- A free Gemini API key from [Google AI Studio](https://aistudio.google.com/app/apikey)
- **Tesseract OCR** installed on your system (a separate program, not a Python
  package) — needed only for the image-upload feature:
  - **Windows:** install from
    [github.com/UB-Mannheim/tesseract/wiki](https://github.com/UB-Mannheim/tesseract/wiki),
    then make sure the install folder (e.g. `C:\Program Files\Tesseract-OCR`) is added
    to your PATH.
  - **Mac:** `brew install tesseract`
  - **Linux:** `sudo apt-get install tesseract-ocr`

  If you skip this, everything else still works — you just can't upload images.

## 2. Setup

```bash
git clone <your-repo-url>
cd survey_gpt
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

Open `.env` and paste your key:

```
GEMINI_API_KEY=your-real-key-here
```

(Optional) Put any lecture-note or textbook PDFs you're allowed to use into the
`docs/` folder — SurveyGPT will retrieve relevant passages automatically.

## 3. Run

Web chat, with image upload for OCR (opens in your browser):

```bash
python main.py
```

Terminal chat (text only, no image upload):

```bash
python main.py --cli
```

## 4. Project layout

```
survey_gpt/
├── main.py            # entry point: CLI + web app, OCR handling
├── tools.py            # calculator functions + the matplotlib chart tool
├── rag.py              # optional retrieval over docs/*.pdf
├── requirements.txt
├── .env.example         # template - copy to .env, never commit the real .env
├── .gitignore
└── docs/               # put your course PDFs here (ignored by git)
```

## 5. Notes and limitations

- If you get a "model not found" error, list the models your key can access:
  `python -c "from google import genai; [print(m.name) for m in genai.Client().models.list()]"`
  and set `SURVEYGPT_MODEL` in `.env` to one of them.
- Only text-based PDFs are indexed for the notes feature; scanned pages need OCR too.
- If image upload gives a "tesseract is not installed" error, double-check the
  Tesseract install step above and that it's on your system PATH.
- Everyone using this app in one running session shares the same conversation history
  (there's just one chat object) — fine for solo use, but keep that in mind if you
  deploy it for multiple people at once.
- Always verify important answers against your textbook.
