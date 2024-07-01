import docx
import os
from pathlib import Path
import PyPDF2
from yaspin import yaspin
import requests
import json

# Ollama Setup
model = 'llama3:8b-instruct-fp16'  # Update with your desired Ollama model
ollama_url = 'http://localhost:11434/api/generate'  # Adjust if needed


def read_word_document(file_path):
    doc = docx.Document(file_path)
    return '\n'.join([para.text for para in doc.paragraphs])


def read_pdf_document(file_path):
    with open(file_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        return '\n'.join([page.extract_text() for page in reader.pages])


def analyze_with_ollama(content, prompt_template, model=model, max_tokens=300):
    prompt = prompt_template.replace("{content}", content)

    def generate_response(prompt, context=[]):
        data = {
            'model': model,
            'prompt': prompt,
            'context': context,
            'max_tokens': max_tokens
        }
        response = requests.post(ollama_url, json=data, stream=True)
        response.raise_for_status()
        response_parts = []
        for line in response.iter_lines():
            if line:
                body = json.loads(line)
                response_part = body.get('response', '')
                response_parts.append(response_part)
                if body.get('done', False):
                    return ''.join(response_parts), body['context']
                if 'error' in body:
                    raise Exception(body['error'])

    response, _ = generate_response(prompt)
    return response


def write_analysis_to_file(analysis, file_path):
    with open(file_path, 'w') as file:
        file.write(analysis)


def extract_email_from_filename(filename):
    return Path(filename).stem


def find_matching_files(folder_path):
    files = os.listdir(folder_path)
    matched_files = {}
    for file in files:
        if file.endswith('.docx') or file.endswith('.pdf'):
            email = extract_email_from_filename(file)
            if email not in matched_files:
                matched_files[email] = []
            matched_files[email].append(file)
    return matched_files


def process_documents_in_folder(folder_path, prompt_template, model=model, max_tokens=300):
    if not os.path.exists(folder_path):
        print(f"The folder {folder_path} does not exist.")
        return

    matched_files = find_matching_files(folder_path)

    for email in matched_files:
        file_list = matched_files[email]
        combined_content = ''
        for file_name in file_list:
            document_path = os.path.join(folder_path, file_name)
            print(f"Processing {document_path}...")
            if file_name.endswith('.docx'):
                content = read_word_document(document_path)
            elif file_name.endswith('.pdf'):
                content = read_pdf_document(document_path)
            combined_content += content + '\n\n'

        if combined_content:
            with yaspin(text="Analyzing documents...", color="magenta") as spinner:
                analysis = analyze_with_ollama(combined_content, prompt_template, model, max_tokens)
                spinner.ok("✓")

            analysis_file_path = os.path.join(folder_path, f"{email}_GAP_analysis.txt")
            write_analysis_to_file(analysis, analysis_file_path)
            print(f"Analysis report created: {analysis_file_path}")
        else:
            print(f"No content found for email {email}. Skipping analysis.")


def main():
    prompt_template = "Analyze the following text and provide a GAP analysis report. Also give me a summary of missing information with possible solutions based on our marketing services. Order the possible solutions you suggest at the end in the order they are best excecuted in. In the GAP analysis report, try to guide them with judgement based on what they entered even if the information is insufficient. Be sure to provide feedback for all nine sections of the marketing plan process: {content}"
    process_documents_in_folder('docs', prompt_template)


if __name__ == "__main__":
    main()