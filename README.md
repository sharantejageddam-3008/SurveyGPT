# SurveyGPT

A Q&A and problem-solving assistant for undergraduate **Surveying** (Civil Engineering) —
built as a Google Colab notebook for a course assignment at IIT Bhubaneswar.

SurveyGPT answers both theory questions and numerical problems covering:
chain & tape surveying, compass surveying, levelling, theodolite & traverse
computation, tacheometry, and curves & area computation.

## How it works

- **Gemini** (Google's LLM) reads the question and writes the explanation, guided by
  a system prompt that keeps it focused on the Surveying syllabus.
- **Python calculator tools** handle the actual arithmetic (bearings, levelling
  reductions, traverse adjustment, curve elements, etc.), since language models are
  unreliable at long calculations — Gemini picks the right tool and lets Python do the
  math.
- **Optional notes retrieval (RAG)** — upload your own lecture-note PDFs in the
  notebook and answers will quote the relevant passages.
- **Gradio** provides the chat interface, with a shareable public link and a private
  conversation per visitor.

## How to run it

1. Open `SurveyGPT.ipynb` in [Google Colab](https://colab.research.google.com)
   (or click the file above and choose "Open in Colab").
2. Get a free API key from [Google AI Studio](https://aistudio.google.com/app/apikey).
3. In Colab, click the 🔑 **Secrets** icon in the left sidebar, add a secret named
   `GEMINI_API_KEY`, paste your key, and turn on notebook access.
4. Run every cell from top to bottom.
5. (Optional) Upload course PDFs when prompted for notes-aware answers.
6. The last cell opens a chat window and prints a public `gradio.live` link you can
   share with anyone — each visitor gets their own private conversation.

## Limitations

- Only text-based PDFs are supported for the notes feature; scanned pages need OCR
  first.
- The public Gradio link expires after about a week, or immediately if the Colab
  runtime disconnects.
- Answers should be verified against your textbook for anything exam-critical.

## Project context

Built as an assignment for the Surveying course, B.Tech Civil Engineering,
IIT Bhubaneswar.
