from datetime import date, datetime, timedelta
import uuid
from pathlib import Path
from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session
from typing import Type


# --------------------- COMMIT HELPER ---------------------
async def commit_db(db: Session):
    db.commit()


# --------------------- CREATE ---------------------
async def insert_record(model: Type, db: Session, **kwargs):
    instance = model(**kwargs)
    db.add(instance)
    await commit_db(db)
    db.refresh(instance)
    return instance

async def insert_record_flush(model: Type, db: Session, **kwargs):
    instance = model(**kwargs)
    db.add(instance)
    
    db.flush()
    return instance


# --------------------- UPDATE ---------------------
async def update_record(id: int, model: Type, db: Session, **kwargs):
    instance = db.query(model).filter(model.id == id).first()

            
    if not instance:
        raise HTTPException(status_code=404, detail=f"{model.__name__} with id {id} not found")

    kwargs.pop("created_at", None)
    
    for key, value in kwargs.items():
        
        if hasattr(instance, key):
            setattr(instance, key, value)

    await commit_db(db)
    db.refresh(instance)
    return instance


# --------------------- DELETE ---------------------
async def delete_record(id: int, model: Type, db: Session):
    instance = db.query(model).filter(model.id == id).first()

    if not instance:
        raise HTTPException(status_code=404, detail=f"{model.__name__} with id {id} not found")

    db.delete(instance)
    await commit_db(db)
    return instance


# --------------------- GET BY ID ---------------------
async def get_record_by_id(id: int, model: Type, db: Session):
    instance = db.query(model).filter(model.id == id).first()
    return instance


# --------------------- GET BY FILTER ---------------------
async def get_record(model: Type, db: Session, **kwargs):
    instance = db.query(model).filter_by(**kwargs).first()
    return instance


async def get_records(model: Type, db: Session, **kwargs):
    instance = db.query(model).filter_by(**kwargs).all()
    return instance

# --------------------- SAVE ONE IMAGE ---------------------
async def save_image(image: UploadFile, sub_static_dir: str):
    if not image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    static_dir = Path(f"app/static/{sub_static_dir}")
    static_dir.mkdir(parents=True, exist_ok=True)

    extension = image.filename.split(".")[-1]
    filename = f"{uuid.uuid4()}.{extension}"
    file_path = static_dir / filename

    content = await image.read()  # async read from UploadFile
    with open(file_path, "wb") as buffer:
        buffer.write(content)

    return f"static/{sub_static_dir}/{filename}"


# --------------------- SAVE MULTIPLE IMAGES ---------------------
async def save_images(images: list[UploadFile], sub_static_dir: str):
    image_urls = []
    for img in images:
        image_url = await save_image(img, sub_static_dir)
        image_urls.append(image_url)
    return image_urls


