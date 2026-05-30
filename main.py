import os 
import pathlib
import shutil
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from google import genai
from fastapi.staticfiles import StaticFiles

app.mount("/", StaticFiles(directory="static", html=True), name="static")

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY)

app = FastAPI()

# Enable CORS so your frontend can communicate with the backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

# --- KEEPS YOUR EXACT ORIGINAL LOGIC COMPLETELY INTACT ---

def scan_project(folder_path):
    folder = pathlib.Path(folder_path)
    if not folder.exists() or not folder.is_dir():
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

def generate_readme(folder_name, languages, file_names):
    prompt = f"""
    You are a technical writer. Generate a professional and detailed README.md for a software project with the following details:
    
    Project Name: {folder_name}
    Detected Languages/Stack: {", ".join(languages) if languages else "Unknown"}
    Files in Project: {", ".join(file_names) if file_names else "None Found"}
    
    The README should include the following sections:
    - Project Title and short description
    - Features
    - Tech Stack
    - Project Structure
    - Installation Instructions
    - Usage Instructions
    - License Information
    
    Write it in clean Markdown format, using appropriate headings, bullet points, and code blocks where necessary. Make it informative and engaging for potential users and contributors. Be specific and realistic based on the project details provided. DON'T INCLUDE ANY EMOJIS AND EM DASHES.
    """
    response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
    try:
        return response.text
    except Exception as e:
        print(f"Failed to generate README: {e}")
        return None

# --- NEW WEB ENDPOINT LOGIC ---

@app.post("/generate")
async def web_generate(files: list[UploadFile] = File(...)):
    """Receives files dropped from the web dashboard, scans them, and returns the markdown."""
    TEMP_DIR = pathlib.Path("./temp_project")
    if TEMP_DIR.exists():
        shutil.rmtree(TEMP_DIR)
    TEMP_DIR.mkdir(parents=True, exist_ok=True)

    # Reconstruct the project folder structure locally from the upload
    project_name = "Uploaded_Project"
    for file in files:
        if file.filename:
            # Extract folder name if provided by browser context path
            parts = pathlib.Path(file.filename).parts
            if len(parts) > 1:
                project_name = parts[0]
                
            file_path = TEMP_DIR / file.filename
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

    # Use your original logic functions on our temporary layout
    languages, file_names = scan_project(TEMP_DIR)
    
    if languages is None:
        return {"error": "Failed to process project folder structures."}

    readme_markdown = generate_readme(project_name, languages, file_names)
    
    # Cleanup temporary folder
    shutil.rmtree(TEMP_DIR)

    return {"markdown": readme_markdown}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)