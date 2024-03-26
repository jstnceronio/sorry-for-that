import base64
import time
import os
import win32com.client

import PIL.ImageGrab
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import openai
from dotenv import load_dotenv
import requests
import pyperclip as pc
from datetime import datetime

# Configuration
picturefilepath = os.path.join("C:\\Users\\asael\\Downloads\\")
WATCH_DIRECTORY = picturefilepath  # os.path.join(".", "img")
load_dotenv(".env")
API_KEY = os.environ.get("OPENAI_API_KEY")
openai.api_key = os.environ.get("OPENAI_API_KEY")
WOLFRAM_API_URL = 'http://api.wolframalpha.com/v2/query'
WOLFRAM_API_KEY = os.environ.get("WOLFRAM_API_KEY")


class ScreenshotEventHandler(FileSystemEventHandler):

    # txtoclipboard checks if result isn't on clipboard and if no copies result to clipboard.
    # After this it makes a notification with the keyboard press Capslock and prints a report.
    def txt_to_clipboard(self, result):
        p = True
        while p:
            if result != pc.paste():
                pc.copy(str(result))
                if result == pc.paste():
                    shell = win32com.client.Dispatch("WScript.Shell")
                    shell.SendKeys("{CAPSLOCK}")  # Press Capslock to lock
                    time.sleep(1)  # time for User to recognize the Capslock
                    shell.SendKeys("{CAPSLOCK}")  # Press Capslock to unlock
                    print("Answer successfully copied to clipboard")  # Report of txtoclipboard
                p = False

    # picturesave Observes the clipboard for new pictures in it. If detected the picture gets saved.
    # The Folder location gets set by the variable picturefilepath. The name is a Timestamp (Hours, Minutes, Seconds)
    # At the end picturesave prints a report of the operation.
    def safe_picture(self, picturefilepath):
        rx = PIL.ImageGrab.grabclipboard()  # initialises rx for observing function.
        now = datetime.now()  # Something for the timestamp
        p = True
        while p:
            if rx != PIL.ImageGrab.grabclipboard():  # check for new pictures in clipboard
                rx = PIL.ImageGrab.grabclipboard()
                time = now.strftime("%H_%M_%S")  # gets timestamp
                fp = picturefilepath + time + ".png"  # builds filename& path
                rx.save(fp)  # saves clipboard
                rx.close()  # closes picture
                print("Picture successfully saved.", fp)  # reports operation
                p = False  # kills while loop

    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith(('.png', '.jpg', '.jpeg')):
            time.sleep(1)
            print(f"Screenshot detected: {event.src_path}")
            self.process_screenshot(event.src_path)

    def process_screenshot(self, filepath):
        base64_image = self.encode_image(filepath)
        gpt_response = self.send_image_to_chatgpt(base64_image)
        print(f"ChatGPT Response: {gpt_response}")
        wolfram_response = self.query_wolfram_alpha(gpt_response)
        result = self.parse_wolfram_response(wolfram_response)
        print("Solution:", result)
        self.txt_to_clipboard(result)

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

    while True:
        event_handler = ScreenshotEventHandler()
        observer = Observer()
        observer.schedule(event_handler, WATCH_DIRECTORY, recursive=False)
        observer.start()  # starts file observer
        print(f"Monitoring {WATCH_DIRECTORY} for new screenshots...")  # prints file observer startup
        event_handler.safe_picture(picturefilepath)  # starts Clipboard observer
        observer.stop()  # kills observer funktion to ensure that only one observer exsists at the time.
        time.sleep(1)  # saefty sleep to ensure, that txtoclipboard and its function pyperclip has finished truly
        # and doesn't interact with PIL.ImageGrab.grabclipboard from picturesave.
