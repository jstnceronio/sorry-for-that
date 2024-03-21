import base64
import time
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import openai
from dotenv import load_dotenv
import requests

# Configuration
WATCH_DIRECTORY = os.path.join(".", "img")
load_dotenv(".env")
API_KEY = os.environ.get("OPENAI_API_KEY")
openai.api_key = os.environ.get("OPENAI_API_KEY")
WOLFRAM_API_URL = 'http://api.wolframalpha.com/v2/query'
WOLFRAM_API_KEY = os.environ.get("WOLFRAM_API_KEY")


class ScreenshotEventHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith(('.png', '.jpg', '.jpeg')):
            print(f"Screenshot detected: {event.src_path}")
            self.process_screenshot(event.src_path)

    def process_screenshot(self, filepath):
        base64_image = self.encode_image(filepath)
        gpt_response = self.send_image_to_chatgpt(base64_image)
        print(f"ChatGPT Response: {gpt_response}")
        wolfram_response = self.query_wolfram_alpha(gpt_response)
        result = self.parse_wolfram_response(wolfram_response)
        print("Solution:", result)

    def query_wolfram_alpha(self, query):
        params = {
            'input': query,
            'format': 'plaintext',
            'output': 'JSON',
            'appid': WOLFRAM_API_KEY,
        }
        response = requests.get(WOLFRAM_API_URL, params=params)
        response.raise_for_status()  # Raises an HTTPError if the response code was unsuccessful
        return response.json()

    def parse_wolfram_response(self, response):
        try:
            pods = response['queryresult']['pods']
            for pod in pods:
                if pod['title'] == 'Result':
                    return pod['subpods'][0]['plaintext']
        except (KeyError, IndexError):
            return "Couldn't find a solution."

    '''
    def extract_text_from_image(self, image_path):

        try:
            image = Image.open(image_path)
            text = pytesseract.image_to_string(image)
            return text
        except Exception as e:
            print(f"Error during OCR processing: {e}")
            return None
    '''

    def encode_image(self, image_path):
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    def send_image_to_chatgpt(self, base64_image):

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_KEY}"
        }

        payload = {
            "model": "gpt-4-vision-preview",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Your task is to prepare a correctly formatted prompt for the wolfram api in order to solve given math problem. You shall only return the prompt without explenation that I then will send to the Wolfram API"
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            "max_tokens": 300
        }
        try:
            response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
            return response.json()['choices'][0]['message']['content']
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