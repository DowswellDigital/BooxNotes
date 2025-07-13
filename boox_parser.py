# boox_parser.py
import os
import openai
import json
from datetime import datetime
import shutil
import subprocess
import base64
import io

# Load API key from .env file
from dotenv import load_dotenv
load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")

RAW_FOLDER = os.path.expanduser("~/Dropbox/BooxNotes/Raw")
OUTPUT_FOLDER = os.path.expanduser("~/Dropbox/BooxNotes/Processed")
MARKDOWN_FOLDER = os.path.expanduser("~/Documents/Vault/Sources/boox")
PROCESSED_LOG = os.path.expanduser("~/Scripts/BooxNotes/processed.json")

if os.path.exists(PROCESSED_LOG):
    with open(PROCESSED_LOG, "r") as f:
        processed_files = set(json.load(f))
else:
    processed_files = set()


def notify(message):
    subprocess.run([
        "osascript", "-e",
        f'display notification "{message}" with title "Boox Watcher"'
    ])



from PIL import Image
from pdf2image import convert_from_path

def summarize_pdf(file_path):
    print(f"🧠 Converting PDF to images: {file_path}")
    images = convert_from_path(file_path)

    print(f"🖼️ Sending {len(images)} page(s) to GPT-4o...")
    image_messages = [
        {
            "type": "text",
            "text": "Please summarize the following handwritten notes into clean, structured Markdown for study purposes."
        }
    ]

    for img in images:
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        image_messages.append({
            "type": "image_url",
            "image_url": {
                "url": "data:image/png;base64," + base64.b64encode(img_bytes.read()).decode('utf-8'),
                "detail": "high"
            }
        })

    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=[{
            "role": "user",
            "content": image_messages
        }]
    )

    return response.choices[0].message.content



def process_pdfs():
    for filename in os.listdir(RAW_FOLDER):
        if not filename.lower().endswith(".pdf"):
            continue
        if filename in processed_files:
            print(f"⏭ Skipping already processed file: {filename}")
            continue

        full_path = os.path.join(RAW_FOLDER, filename)
        print(f"\U0001F4A1 Summarizing: {filename}")

        try:
            summary = summarize_pdf(full_path)

            # Save summary to markdown
            basename = os.path.splitext(filename)[0]
            markdown_path = os.path.join(MARKDOWN_FOLDER, f"{basename}.md")
            with open(markdown_path, "w") as md:
                md.write(f"---\ntitle: {basename}\ntags: [boox, notes]\n---\n\n")
                md.write(summary)

            # Move original PDF to archive
            shutil.move(full_path, os.path.join(OUTPUT_FOLDER, filename))

            # Log success
            processed_files.add(filename)
            with open(PROCESSED_LOG, "w") as f:
                json.dump(list(processed_files), f)

            print(f"✅ Processed {filename}\n")
            notify(f"Processed: {filename}")

        except Exception as e:
            print(f"❌ Error processing {filename}: {e}")
            notify(f"⚠️ Error processing {filename}")
