import io
import time
import os
import hashlib
import base64
import win32com.client
from PIL import ImageGrab
import openai
from dotenv import load_dotenv
import requests
import pyperclip as pc
# import pyfiglet
from pathlib import Path


def image_to_hash(img):
    """Convert an image to a hash for easy comparison."""
    hash_obj = hashlib.sha256()
    hash_obj.update(img.tobytes())
    return hash_obj.hexdigest()


class ClipboardImageHandler:
    def __init__(self):
        self.last_hash = None

    def check_clipboard_for_screenshot(self):
        """Check the clipboard for images and process if it's a new screenshot."""
        try:
            img = ImageGrab.grabclipboard()  # Try to get an image from the clipboard
            if img is not None:
                current_hash = image_to_hash(img)
                if current_hash != self.last_hash:
                    print("New screenshot detected in the clipboard!")
                    self.process_screenshot(img)
                    self.last_hash = current_hash
                else:
                    print("Duplicate screenshot detected. Not processing.")
        except Exception as e:
            print("Error:", e)

    def process_screenshot(self, img):
        base64_image = self.encode_image(img)
        gpt_response = self.send_image_to_chatgpt(base64_image)
        print(f"ChatGPT Response: {gpt_response}")
        # wolfram_response = self.query_wolfram_alpha(gpt_response)
        # result = self.parse_wolfram_response(wolfram_response)

        pc.copy(self.get_last_line(str(gpt_response)))
        shell = win32com.client.Dispatch("WScript.Shell")
        shell.SendKeys("{CAPSLOCK}")  # Press Capslock to lock
        time.sleep(2)  # time for User to recognize the Capslock
        shell.SendKeys("{CAPSLOCK}")  # Press Capslock to unlock
        # print("Solution:", result)
        print("Answer successfully copied to clipboard")  # Report of txtoclipboard

    def encode_image(self, img):
        """Encode image object to base64, converting RGBA to RGB if necessary."""
        if img.mode != 'RGB':
            img = img.convert('RGB')  # Convert RGBA to RGB
        buffered = io.BytesIO()
        img.save(buffered, format="JPEG")
        return base64.b64encode(buffered.getvalue()).decode('utf-8')

    def get_last_line(self, text):
        # Split the text into lines
        lines = text.splitlines()
        # Return the last line
        return lines[-1] if lines else ''

    def send_image_to_chatgpt(self, base64_image):
        """Send base64 encoded image to ChatGPT."""
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {OPENAI_API_KEY}"
        }
        payload = {
            "model": "gpt-4o",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Löse die folgende Gleichung. Nenne die Antwort immer in der letzten Zeile."
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
            "max_tokens": 600
        }
        try:
            response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
            return response.json()['choices'][0]['message']['content']
        except Exception as e:
            print(f"Error sending text to ChatGPT: {e}")
            return None

    def query_wolfram_alpha(self, query):
        """Query Wolfram Alpha with given query string."""
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
        """Parse response from Wolfram Alpha."""
        try:
            pods = response['queryresult']['pods']
            for pod in pods:
                if pod['title'] == 'Result':
                    return pod['subpods'][0]['plaintext']
        except (KeyError, IndexError):
            return "Couldn't find a solution."


if __name__ == "__main__":
    handler = ClipboardImageHandler()
    # print(pyfiglet.figlet_format("Sorry for that"))
    print("You are using the windows version of 'Sorry for that', welcome!")

    dotenv_file = Path('.env')

    if not dotenv_file.is_file():
        print("It seems like you're using 'Sorry for that' for the first time")
        print("Let's create an environment file to store your API keys")
        OPENAI_API_KEY = input('Enter your Chat GPT API Key: ')
        WOLFRAM_API_KEY = input('Enter your Wolfram Alpha API Key: ')
        file_name = '.env'
        f = open(file_name, 'a+')  # open file in append mode
        f.write('OPENAI_API_KEY=' + OPENAI_API_KEY + '\n')
        f.write('WOLFRAM_API_KEY=' + WOLFRAM_API_KEY)
        f.close()
    else:
        print("We're sorted. Let's get started.")

    # Configuration
    load_dotenv(".env")
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
    openai.api_key = OPENAI_API_KEY
    WOLFRAM_API_URL = 'http://api.wolframalpha.com/v2/query'
    WOLFRAM_API_KEY = os.environ.get("WOLFRAM_API_KEY")

    print("Monitoring clipboard for screenshots. Press Ctrl+C to exit. \n")
    try:
        while True:
            handler.check_clipboard_for_screenshot()
            time.sleep(1)  # Check every 1 second
    except KeyboardInterrupt:
        print("Exited by user. ")
