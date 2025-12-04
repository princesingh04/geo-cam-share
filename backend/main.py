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

# Mount the uploads directory to serve images
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

@app.get("/gallery")
def gallery():
    images = [f for f in os.listdir(UPLOAD_DIR) if f.endswith(('.jpg', '.png', '.jpeg'))]
    images.sort(reverse=True) # Newest first
    
    log_content = ""
    if os.path.exists(os.path.join(UPLOAD_DIR, "locations.log")):
        with open(os.path.join(UPLOAD_DIR, "locations.log"), "r") as f:
            log_content = f.read()

    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>GeoCam Gallery</title>
        <style>
            body { font-family: sans-serif; padding: 20px; }
            .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 20px; }
            .card { border: 1px solid #ddd; padding: 10px; border-radius: 8px; }
            img { max-width: 100%; border-radius: 4px; }
            pre { background: #f4f4f4; padding: 10px; overflow-x: auto; }
        </style>
    </head>
    <body>
        <h1>Captured Data</h1>
        
        <h2>Locations Log</h2>
        <pre>""" + log_content + """</pre>
        
        <h2>Images</h2>
        <div class="grid">
    """
    
    for img in images:
        html_content += f'''
            <div class="card">
                <a href="/uploads/{img}" target="_blank">
                    <img src="/uploads/{img}" loading="lazy">
                </a>
                <p>{img}</p>
            </div>
        '''
        
    html_content += """
        </div>
    </body>
    </html>
    """
    from fastapi.responses import HTMLResponse
    return HTMLResponse(content=html_content)

# Mount the frontend directory to serve index.html
# We mount it at the root "/" LAST so it doesn't override other routes
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
