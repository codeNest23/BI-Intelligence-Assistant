"""
PDF Q&A Chatbot
================
Ask questions about any PDF using OpenRouter (GPT-OSS-120B).

Commands:
  - Type a question  -> get an answer grounded ONLY in the PDF
  - 'summarize'      -> get a structured summary of the PDF
  - 'exit' / 'quit'  -> close the program
"""

import os
import sys
import fitz  # PyMuPDF
from openai import OpenAI, APIError, APIConnectionError, APIStatusError
from dotenv import load_dotenv

# =============================================
# 1. LOAD ENVIRONMENT & INIT CLIENT
# =============================================
load_dotenv()

api_key = os.getenv("OPEN_ROUTER_API_KEY")
if not api_key:
    print("[ERROR] OPEN_ROUTER_API_KEY not found in .env file.")
    sys.exit(1)

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key,
)

MODEL = "openai/gpt-oss-120b:free"

# =============================================
# 2. SYSTEM PROMPT TEMPLATE
# =============================================
SYSTEM_PROMPT_TEMPLATE = (
    "You are a helpful PDF assistant. Answer questions ONLY using the content "
    "of the document provided. Do not use outside knowledge.\n\n"
    "If the answer is not in the document, say:\n"
    "\"I could not find this information in the document.\"\n\n"
    "For summaries, respond with:\n"
    "  Overview: [brief overview]\n"
    "  Key Points: [bullet list]\n"
    "  Conclusion: [final takeaway]\n\n"
    "Always cite the section or page when possible.\n\n"
    "The document content is provided below:\n\n"
    "{pdf_text}"
)

# =============================================
# 3. PDF TEXT EXTRACTION
# =============================================
def extract_pdf_text(pdf_path):
    """
    Extract all text from a PDF using PyMuPDF (fitz).
    Returns combined text with page markers.
    Raises FileNotFoundError or ValueError on failure.
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError("PDF file not found: '{}'".format(pdf_path))

    if not pdf_path.lower().endswith(".pdf"):
        raise ValueError("The provided file does not have a .pdf extension.")

    doc = fitz.open(pdf_path)
    pages_text = []

    for page_num, page in enumerate(doc, start=1):
        text = page.get_text().strip()
        if text:
            pages_text.append("--- Page {} ---\n{}".format(page_num, text))

    doc.close()

    if not pages_text:
        raise ValueError(
            "No extractable text found in this PDF.\n"
            "It may be a scanned image PDF. Please use an OCR tool first\n"
            "(e.g. Adobe Acrobat, Tesseract) to make it text-searchable."
        )

    return "\n\n".join(pages_text)


# =============================================
# 4. AI QUERY FUNCTION
# =============================================
def ask_ai(system_prompt, user_message):
    """
    Send a message to OpenRouter and return the assistant reply.
    Handles API errors gracefully.
    """
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_message},
            ],
        )

        if not response.choices or not response.choices[0].message.content:
            return "[ERROR] The AI returned an empty response. Please try again."

        return response.choices[0].message.content.strip()

    except APIConnectionError:
        return "[ERROR] Could not connect to OpenRouter. Check your internet connection."
    except APIStatusError as e:
        return "[ERROR] API returned status {}: {}".format(e.status_code, e.message)
    except APIError as e:
        return "[ERROR] API error: {}".format(e)
    except Exception as e:
        return "[ERROR] Unexpected error: {}".format(e)


# =============================================
# 5. PRINT BANNER
# =============================================
def print_banner():
    print("=" * 60)
    print("         PDF Q&A Chatbot")
    print("         Powered by OpenRouter / GPT-OSS-120B")
    print("=" * 60)
    print("Commands:")
    print("  - Type any question  => answered from the PDF only")
    print("  - 'summarize'        => structured PDF summary")
    print("  - 'exit' / 'quit'    => close the program")
    print("=" * 60)


# =============================================
# 6. MAIN LOOP
# =============================================
def main():
    print_banner()

    # -- Step 1: Get PDF path from user --
    pdf_text = None
    system_prompt = None

    while pdf_text is None:
        pdf_path = input("\nEnter the full path to your PDF file: ").strip().strip('"').strip("'")

        if pdf_path.lower() in ("exit", "quit"):
            print("Goodbye!")
            sys.exit(0)

        try:
            print("\nExtracting text from '{}'...".format(os.path.basename(pdf_path)))
            pdf_text = extract_pdf_text(pdf_path)
            system_prompt = SYSTEM_PROMPT_TEMPLATE.format(pdf_text=pdf_text)

            page_count = pdf_text.count("--- Page ")
            print("[OK] Successfully loaded {} page(s) of text.".format(page_count))
            print("     Total characters extracted: {:,}".format(len(pdf_text)))

        except FileNotFoundError as e:
            print("\n[ERROR] {}".format(e))
            print("        Please check the path and try again.")

        except ValueError as e:
            print("\n[ERROR] {}".format(e))
            retry = input("Try a different file? (y/n): ").strip().lower()
            if retry != "y":
                print("Goodbye!")
                sys.exit(0)

    # -- Step 2: Q&A loop --
    print("\nPDF loaded! You can now ask questions. Type 'exit' to quit.\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\nSession ended. Goodbye!")
            break

        if not user_input:
            continue

        command = user_input.lower()

        # Exit
        if command in ("exit", "quit"):
            print("Goodbye!")
            break

        # Summarize
        if command == "summarize":
            print("\n[Generating summary...]\n")
            message = (
                "Please provide a structured summary of this document with: "
                "Overview, Key Points (as bullet list), and Conclusion."
            )
        else:
            message = user_input

        # Call AI
        answer = ask_ai(system_prompt, message)
        print("\nAssistant:\n{}\n".format(answer))
        print("-" * 60)


# =============================================
# ENTRY POINT
# =============================================
if __name__ == "__main__":
    main()