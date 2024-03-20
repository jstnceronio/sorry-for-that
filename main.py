import time
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from PIL import Image
import pytesseract
import openai
from dotenv import load_dotenv

# Configuration
WATCH_DIRECTORY = os.path.join(".", "img")
load_dotenv(".env")
openai.api_key = os.environ.get("OPEN_API_KEY")


class ScreenshotEventHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith(('.png', '.jpg', '.jpeg')):
            print(f"Screenshot detected: {event.src_path}")
            self.process_screenshot(event.src_path)

    def process_screenshot(self, filepath):
        text = self.extract_text_from_image(filepath)
        if text:
            print(f"Extracted Text: {text}")
            response = self.send_text_to_chatgpt(text)
            print(f"ChatGPT Response: {response}")
        else:
            print("No text found in the screenshot.")

    def extract_text_from_image(self, image_path):
        try:
            image = Image.open(image_path)
            text = pytesseract.image_to_string(image)
            return text
        except Exception as e:
            print(f"Error during OCR processing: {e}")
            return None

    def send_text_to_chatgpt(self, text):
        try:
            response = openai.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "system", "content": "You are a calculator, you only return the solution."},
                          {"role": "user", "content": text}]
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error sending text to ChatGPT: {e}")
            return None


if __name__ == "__main__":
    event_handler = ScreenshotEventHandler()
    observer = Observer()
    observer.schedule(event_handler, WATCH_DIRECTORY, recursive=False)
    observer.start()
    print(f"Monitoring {WATCH_DIRECTORY} for new screenshots...")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
