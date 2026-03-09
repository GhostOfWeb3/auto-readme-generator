import os 
import pathlib
from pickle import GET
from dotenv import load_dotenv
from google import genai

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY)

LANGUAGE_MAP = {
    ".py": "Python",
    ".rs": "Rust",
    ".js": "JavaScript",
    ".cpp": "C++",
    ".ts": "TypeScript",
    ".java": "Java",
    ".go": "Go",
    ".html": "HTML",
    ".css": "CSS",
    ".json": "JSON",
    ".toml": "TOML",
    ".cs": "C#",
}

def scan_project(folder_path):
    folder = pathlib.Path(folder_path)
    
    if not folder.exists() or not folder.is_dir():
        print(f"Invalid folder path: {folder_path}")
        return None, None
    
    detected_languages = set()
    file_names = []
    ignored = {".git", "node_modules", "venv", "__pycache__", ".env"}
    
    for item in folder.rglob("*"):
        if any(part in ignored for part in item.parts):
            continue
        if item.is_file():
            file_names.append(item.name)
            suffix = item.suffix.lower()
            if suffix in LANGUAGE_MAP:
                detected_languages.add(LANGUAGE_MAP[suffix])
                
    return list(detected_languages), file_names

def generate_readme(folder_path, languages, file_names):
    folder_name = pathlib.Path(folder_path).name
    prompt = f"""
    You are a technical writer. Generate a professional and detailed README.md for a software project with the following details:
    
    Project Name: {folder_name}
    Detected Languages/Stack: {", ".join(languages) if languages else "Unknown"}
    Files in Project: {", ".join(file_names) if file_names else "None Found"}
    
    The README should include the following sections:
    - roject Title and short description
    - Features
    - Tech Stack
    - Project Structure
    - Installation Instructions
    - Usage Instructions
    License Information
    
    Write it in clean Markdown format, using appropriate headings, bullet points, and code blocks where necessary. Make it informative and engaging for potential users and contributors. Be specific and realistic based on the project details provided. DON'T INCLUDE ANY EMOJIS AND EM DASHES.
    """
    response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
    
    try:
        return response.text
    except Exception as e:
        print(f"Failed to generate README: {e}")
        return None

def save_readme(folder_path, content):
    output_path = pathlib.Path(folder_path) / "README.md"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"README.md saved to {output_path}")
    
def main():
    folder_path = input("Enter the path to your project folder: ").strip()
    
    print("Scanning project...")
    languages, file_names = scan_project(folder_path)
    
    if languages is None:
        return
    
    print(f"Detected: {', '.join(languages) if languages else 'No Known languages found'}")
    print("Generating README...")
    
    readme_content = generate_readme(folder_path, languages, file_names)
    
    if readme_content:
        save_readme(folder_path, readme_content)
    else:
        print("README generation failed.")
        
if __name__ == "__main__":
    main()