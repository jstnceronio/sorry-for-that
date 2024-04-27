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


class ClipboardImageHandler:

    PROMPT = ('Gegeben sind entweder ein französisches Verb und weitere Angaben oder ein deutsches Verb, '
              'Im Falle des französischen Verbes, konjugiere das folgende Verb gemäss Vorgaben. '
              'Im Falle des deutschen Verbes, übersetze es auf französisch. '
              'Antworte nur immer nur mit der eigentlichen Antwort')


    def __init__(self):
        self.last_hash = None

    def send_text_to_chatgpt(self, question):
        """Send base64 encoded image to ChatGPT."""
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {OPENAI_API_KEY}"
        }
        payload = {
            "model": "gpt-4",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"{self.PROMPT}: {question}"
                        }
                    ]
                }
            ],
            "max_tokens": 300
        }
        try:
            response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
            self.process_result(response.json()['choices'][0]['message']['content'])
        except Exception as e:
            print(f"Error sending text to ChatGPT: {e}")
            return None

    def process_result(self, result):
        pc.copy('res:' + str(result))
        shell = win32com.client.Dispatch("WScript.Shell")
        shell.SendKeys("{CAPSLOCK}")  # Press Capslock to lock
        time.sleep(2)  # time for User to recognize the Capslock
        shell.SendKeys("{CAPSLOCK}")  # Press Capslock to unlock
        print("Solution:", result)
        print("Answer successfully copied to clipboard")

    def monitor_clipboard(self):
        previous_text = pc.paste()  # Initially check what's in the clipboard
        print("Monitoring clipboard. Press Ctrl+C to stop.")
        try:
            while True:
                current_text = pc.paste()  # Get current clipboard content
                # Check if the clipboard content has changed
                if current_text != previous_text and "res:" not in current_text:
                    print("New clipboard text:", current_text)
                    previous_text = current_text
                    self.send_text_to_chatgpt(current_text)
                time.sleep(1)  # Wait for 1 second before checking again
        except KeyboardInterrupt:
            print("Clipboard monitoring stopped.")


if __name__ == "__main__":
    # Application flow
    # Enter credentials
    # Copy prompt
    # for example:
    """
    Verb:
    vouloir
    Person:	
    2. pers. sing. — tu
    Zeit:	
    indicatif présent actif
    """
    # Send prompt to gpt: "Konjugiere das folgende Verb gemäss Vorgaben, antworte nur mit konjugierten Verb:"
    handler = ClipboardImageHandler()
    # print(pyfiglet.figlet_format("Sorry for that"))
    print("You are using the windows version of 'Sorry for that', welcome!")

    dotenv_file = Path('.env')

    if not dotenv_file.is_file():
        print("It seems like you're using 'Sorry for that' for the first time")
        print("Let's create an environment file to store your API keys")
        OPENAI_API_KEY = input('Enter your Chat GPT API Key')
        file_name = '.env'
        f = open(file_name, 'a+')  # open file in append mode
        f.write('OPENAI_API_KEY=' + OPENAI_API_KEY + '\n')
        f.close()
    else:
        print("We're sorted. Let's get started.")

    # Configuration
    load_dotenv(".env")
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

    handler.monitor_clipboard()
