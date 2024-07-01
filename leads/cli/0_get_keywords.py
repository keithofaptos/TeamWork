import json
import requests
import csv
import re
import logging
import itertools
import threading
import sys
import time

# Configure logging
logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

# Global variables
model = 'llama3:8b-instruct-fp16'

class Spinner:
    def __init__(self, message, delay=0.1):
        self.spinner = itertools.cycle(['-', '/', '|', '\\'])
        self.delay = delay
        self.message = message
        self.stop_running = threading.Event()
        self.spin_thread = threading.Thread(target=self.initiate_spinner)

    def initiate_spinner(self):
        while not self.stop_running.is_set():
            sys.stdout.write(f"\r{self.message} {next(self.spinner)}")
            sys.stdout.flush()
            time.sleep(self.delay)
        sys.stdout.write('\r')

    def start(self):
        self.spin_thread.start()

    def stop(self):
        self.stop_running.set()
        self.spin_thread.join()
        sys.stdout.write('\r')
        sys.stdout.flush()

def generate(prompt, context):
    """
    Sends a request to the AI model to generate text based on the prompt and context.
    
    :param prompt: The prompt to send to the AI model.
    :param context: The context (previous interactions) for the model to consider.
    :return: The generated text and the updated context.
    """
    spinner = Spinner("AI is thinking...")
    spinner.start()
    
    try:
        response = requests.post(
            'http://localhost:11434/api/generate',
            json={'model': model, 'prompt': prompt, 'context': context},
            stream=True
        )
        response.raise_for_status()

        full_response = ""
        for line in response.iter_lines():
            body = json.loads(line)
            response_part = body.get('response', '')
            full_response += response_part

            if 'error' in body:
                spinner.stop()
                raise Exception(body['error'])

            if body.get('done', False):
                spinner.stop()
                return full_response, body['context']
    except requests.exceptions.RequestException as e:
        spinner.stop()
        logging.error(f"Request to model generation failed: {e}")
        raise SystemExit(e)

def parse_keywords(response):
    """
    Parses keywords from the given response text.
    
    :param response: The text response containing keywords.
    :return: A list of parsed and cleaned keywords.
    """
    # Define a regular expression pattern to find unwanted characters
    # This pattern finds any sequence of digits (\d+) followed by a period and a space
    pattern = re.compile(r'^\d+\.\s*')
    
    # Split the string by newlines to separate each keyword
    raw_keywords = response.split('\n')
    
    # Use regular expression to replace unwanted characters with an empty string
    keywords = [pattern.sub('', keyword.strip()) for keyword in raw_keywords if keyword.strip()]
    
    return keywords

def write_keywords_to_csv(keywords):
    """
    Writes the keywords to a CSV file.
    
    :param keywords: A list of keywords to write to the file.
    """
    filename = "keywords.csv"
    try:
        with open(filename, 'w', newline='') as csvfile:
            csvwriter = csv.writer(csvfile)
            csvwriter.writerow(['Keywords'])  # Header
            for keyword in keywords:
                csvwriter.writerow([keyword])  # Write each keyword in its own row
        print(f"Keywords written to {filename}")
    except IOError as e:
        logging.error(f"File operation failed: {e}")
        raise SystemExit(e)

def main():
    """
    Main function to drive the script.
    """
    context = []  # Conversation history for context awareness
    user_input = input("Enter a seed keyword for variations: ")
    prompt = f"Remember you are writing keywords into a CSV file format. Without numbering or extra quotes, one keyword per line, generate 50 keywords for: {user_input}"
    print("Generating keywords...")
    response, context = generate(prompt, context)
    
    keywords = parse_keywords(response)
    write_keywords_to_csv(keywords)

if __name__ == "__main__":
    main()
