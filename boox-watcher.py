# boox-watcher.py
import time
import os
import sys
import subprocess
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Add parser path
sys.path.append(os.path.expanduser("~/Scripts/BooxNotes"))
from boox_parser import process_pdfs

WATCH_FOLDER = os.path.expanduser("~/Dropbox/BooxNotes/Raw")

def log(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}", flush=True)

def notify(title, message):
    subprocess.run(["osascript", "-e", f'display notification \"{message}\" with title \"{title}\"'])

class BooxHandler(FileSystemEventHandler):
    def on_created(self, event):
        log(f"📁 Event detected: {event.src_path}")
        if event.is_directory:
            log("🚫 Skipped directory.")
            return
        if event.src_path.lower().endswith(".pdf"):
            log(f"📥 New PDF detected: {event.src_path}")
            notify("Boox Watcher", f"New BooxNote Detected: {os.path.basename(event.src_path)}")
            try:
                process_pdfs(event.src_path)
                log(f"✅ Finished processing: {event.src_path}")
                notify("Boox Watcher", f"BooxNote Processing Complete: {os.path.basename(event.src_path)}")
            except Exception as e:
                log(f"❌ Error: {str(e)}")
                notify("Boox Watcher", f"Error processing BooxNote: {os.path.basename(event.src_path)}")
        else:
            log("⚠️ File is not a PDF. Skipping.")

if __name__ == "__main__":
    log(f"👀 Watching folder: {WATCH_FOLDER}")
    event_handler = BooxHandler()
    observer = Observer()
    observer.schedule(event_handler, path=WATCH_FOLDER, recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
