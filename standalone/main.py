"""
SurveyGPT - a Q&A / problem-solving assistant for undergraduate Surveying
(Civil Engineering): chain & tape, compass, levelling, theodolite & traverse,
tacheometry, curves, area computation. Also supports:
  - uploading a photo of a hand-written/printed problem (OCR via Tesseract)
  - asking for a quick chart (matplotlib, returned inline)

Usage:
    python main.py            # web chat window in your browser (default)
    python main.py --cli      # plain text chat in the terminal (no image/OCR support)

Requirements beyond `pip install -r requirements.txt`:
    Tesseract OCR must be installed on your system for the image/OCR feature to work
    (pytesseract is just a wrapper around the real `tesseract` program). See README.md.
"""

import argparse
import os
import sys

from dotenv import load_dotenv
from google import genai
from google.genai import types

from tools import ALL_TOOLS, generate_matplotlib_plot
from rag import NotesIndex

MODEL = os.environ.get("SURVEYGPT_MODEL", "gemini-3.5-flash")

SYSTEM_PROMPT = """You are SurveyGPT, a teaching assistant for the Surveying course of a \
B.Tech Civil Engineering programme.

Scope: introduction & classification of surveys, chain and tape surveying, compass \
surveying and local attraction, plane table surveying, levelling (HI and rise-and-fall, \
reciprocal levelling, curvature and refraction, contouring), theodolite surveying, \
traverse computation (Bowditch/transit), tacheometry, simple/compound/reverse/transition \
curves, areas and volumes, trilateration/triangulation basics, EDM/total station, GPS/GNSS \
and remote sensing basics.

How to answer:
1. For numerical problems: list the given data, state the formula, substitute with units, \
   then give the final answer. Use the provided calculator tools for the arithmetic instead \
   of computing long calculations yourself. You can also generate plots and diagrams using \
   the `generate_matplotlib_plot` tool when appropriate or requested, providing lists of x \
   and y data, the plot type (line, bar, scatter), title, and axis labels.
2. For theory questions: give a clear, exam-oriented explanation with a short example or a \
   sketch description.
3. If course-material excerpts are supplied, prefer them and mention which source you used.
4. If the question is ambiguous or data is missing, ask for exactly what is missing instead \
   of guessing.
5. Use metric units and standard Indian textbook conventions (WCB, RL, chainage). If unsure, \
   say so - never invent facts.
6. Stay within surveying/civil engineering; politely decline unrelated requests.
7. Never use LaTeX or markdown math syntax (no $...$, \\frac{}{}, \\Delta, \\times, ^{}, _{}, \
   etc.) - the chat window cannot render it and it shows up as broken text. Write every \
   formula in plain text with normal keyboard characters instead, e.g. "R * tan(delta / 2)" \
   or "sqrt(x)", and spell out Greek letters (delta, theta) rather than using symbols."""


def get_api_key() -> str:
    """Reads GEMINI_API_KEY from the environment / a .env file, or prompts for it."""
    load_dotenv()  # reads a local .env file if present, without overriding real env vars
    key = os.environ.get("GEMINI_API_KEY")
    if key:
        return key
    if sys.stdin.isatty():
        import getpass

        return getpass.getpass(
            "Paste your Gemini API key (get one at https://aistudio.google.com/app/apikey): "
        )
    raise RuntimeError(
        "GEMINI_API_KEY is not set. Create a .env file (see .env.example) or export it "
        "as an environment variable before running SurveyGPT."
    )


def build_chat():
    """Creates the Gemini client + a chat session with tools and system prompt wired in."""
    client = genai.Client(api_key=get_api_key())
    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT,
        tools=ALL_TOOLS,
        temperature=0.2,
    )
    return client.chats.create(model=MODEL, config=config)


def ocr_image(img_path: str) -> str:
    """Runs OCR on an uploaded image and returns extracted text (empty string on failure)."""
    from PIL import Image
    import pytesseract

    try:
        img = Image.open(img_path)
        return pytesseract.image_to_string(img)
    except Exception as e:  # noqa: BLE001
        print(f"ERROR: OCR failed on {img_path}: {e}")
        return ""


def answer_multimodal(chat, notes: NotesIndex, text_message: str, image_files: list) -> str:
    """Handles one turn: OCR any uploaded images, run retrieval, call Gemini, and
    manually execute any generate_matplotlib_plot tool call the model asks for."""
    ocr_text = []
    for img_path in image_files or []:
        extracted = ocr_image(img_path)
        if extracted.strip():
            ocr_text.append(extracted)

    combined_message = text_message
    if ocr_text:
        combined_message += "\n\n[OCR from image]:\n" + "\n".join(ocr_text)

    if not combined_message.strip():
        return "Please provide a question, either by typing or by uploading an image."

    context, sources = notes.retrieve(combined_message)
    prompt = (
        f"Course material excerpts (use if relevant):\n{context}\n\n---\nStudent question: {combined_message}"
        if context
        else combined_message
    )

    try:
        full_response = chat.send_message(prompt)
        reply_parts = []
        for part in full_response.candidates[0].content.parts:
            if part.text:
                reply_parts.append(part.text)
            elif part.function_call:
                tool_name = part.function_call.name
                tool_args = dict(part.function_call.args.items())
                if tool_name == "generate_matplotlib_plot":
                    try:
                        reply_parts.append(generate_matplotlib_plot(**tool_args))
                    except Exception as tool_e:  # noqa: BLE001
                        reply_parts.append(f"Error executing plotting tool: {tool_e}")
                else:
                    reply_parts.append(f"Tool call: {tool_name} with args {tool_args}")
        reply = "\n".join(reply_parts)
        if not reply.strip():
            reply = "I could not produce an answer - please rephrase or try again."
    except Exception as e:  # noqa: BLE001
        return f"Error while contacting the model: {e}"

    if sources:
        reply += "\n\nNotes retrieved: " + ", ".join(sources)
    return reply


def run_cli():
    print("Loading SurveyGPT (Ctrl+C to quit)...")
    notes = NotesIndex()
    chat = build_chat()
    print(f"Ready. Model: {MODEL}. Put PDFs in ./docs/ for notes-aware answers.")
    print("Note: image/OCR upload is only available in web mode (python main.py).\n")
    while True:
        try:
            message = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye!")
            break
        if not message:
            continue
        if message.lower() in {"quit", "exit"}:
            break
        print("\nSurveyGPT:", answer_multimodal(chat, notes, message, []), "\n")


def run_web():
    import gradio as gr

    notes = NotesIndex()
    chat = build_chat()

    def respond(message, history):
        text_message = message.get("text", "") if isinstance(message, dict) else message
        image_files = message.get("files", []) if isinstance(message, dict) else []
        return answer_multimodal(chat, notes, text_message, image_files)

    demo = gr.ChatInterface(
        respond,
        title="SurveyGPT - Surveying Assistant",
        description="Ask theory questions, paste numerical problems, or upload a photo of a "
        "problem (levelling, traverse, curves, tacheometry...).",
        examples=[
            "Explain the difference between rise and fall method and HI method.",
            "Convert WCB 236 30' to quadrantal bearing and find its back bearing.",
            "A simple circular curve has R = 300 m, deflection angle 60 deg and PI "
            "chainage 1250 m. Find all curve elements.",
            "Compute the closing error and Bowditch adjustment: AB 100 m 0 deg, "
            "BC 80 m 90 deg, CD 100 m 181 deg, DA 80 m 270 deg.",
        ],
        multimodal=True,  # enables the image-upload button for OCR
    )
    demo.launch()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SurveyGPT - a Surveying assistant")
    parser.add_argument("--cli", action="store_true", help="run as a terminal chat instead of a web app")
    args = parser.parse_args()
    (run_cli if args.cli else run_web)()
