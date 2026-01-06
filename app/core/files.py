# app/core/files.py

import os
from uuid import uuid4
from fastapi import UploadFile

UPLOAD_DIR = "app/static/profile_images"

# Ensure directory exists
os.makedirs(UPLOAD_DIR, exist_ok=True)

def save_profile_image(file: UploadFile) -> str:
    """Save uploaded profile image and return the relative path."""
    ext = file.filename.split(".")[-1] if "." in file.filename else "jpg"
    filename = f"{uuid4()}.{ext}"
    path = os.path.join(UPLOAD_DIR, filename)

    # Read file content
    content = file.file.read()
    
    # Save file
    with open(path, "wb") as f:
        f.write(content)

    return f"/static/profile_images/{filename}"