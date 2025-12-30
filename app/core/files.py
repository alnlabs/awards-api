# app/core/files.py

import os
from uuid import uuid4
from fastapi import UploadFile

UPLOAD_DIR = "app/static/profile_images"

def save_profile_image(file: UploadFile) -> str:
    ext = file.filename.split(".")[-1]
    filename = f"{uuid4()}.{ext}"
    path = os.path.join(UPLOAD_DIR, filename)

    with open(path, "wb") as f:
        f.write(file.file.read())

    return f"/static/profile_images/{filename}"