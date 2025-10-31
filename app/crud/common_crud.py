import uuid
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException, UploadFile
from typing import Type, Union
from pathlib import Path

# async image save helper
async def save_image(image: UploadFile, static_subdir: str) -> str:
    if not image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    # Ensure folder exists
    static_dir = Path(f"app/static/{static_subdir}")
    static_dir.mkdir(parents=True, exist_ok=True)

    # Generate random filename
    extension = image.filename.split(".")[-1]
    filename = f"{uuid.uuid4()}.{extension}"
    file_path = static_dir / filename

    # Save file
    content = await image.read()
    with open(file_path, "wb") as buffer:
        buffer.write(content)

    # Return relative URL
    return f"/static/{static_subdir}/{filename}"


def db_commit(db: Session, objs: list = None):
    """
    Safely commits the current transaction.
    Optionally refreshes provided SQLAlchemy model objects.
    """
    try:
        db.commit()
        if objs:
            for obj in objs:
                db.refresh(obj)
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Database commit failed: {str(e)}")


from pathlib import Path
from typing import Type, Union, List
from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

async def upsert_records(
    db: Session,
    model: Type,
    data: Union[dict, object, list],
    image: Union[UploadFile, List[UploadFile], None] = None,
    path: str = None,
    **kwargs
):
    """
    Generic upsert helper function.
    - Updates if record exists (based on kwargs)
    - Creates new if not found
    - Supports single or multiple image uploads
    """

    try:
        if not isinstance(data, (dict, list)):
            data = data.dict()
        if isinstance(data, dict):
            data = [data]

        result_objs = []
        print("UPSERT RESULT:", data)
        if not data:
            raise HTTPException(status_code=500, detail="Upsert returned no data")

        for item in data:
            instance = None
            if kwargs:
                instance = db.query(model).filter_by(**kwargs).first()

            # Handle image uploads
            if image and path:
                if isinstance(image, list):  # multiple images
                    image_urls = []
                    for img in image:
                        image_url = await save_image(img, path)
                        image_urls.append(image_url)
                    item["images"] = image_urls  
                else:  # single image
                    image_url = await save_image(image, path)
                    item["image"] = image_url

                    # delete old image if exists
                    if instance and getattr(instance, "image", None):
                        old_path = Path("app") / instance.image.lstrip("/")
                        if old_path.exists():
                            old_path.unlink(missing_ok=True)

            # Upsert logic
            if instance:
                # Prevent overwriting created_at
                item.pop("created_at", None)
    
                for key, value in item.items():
                    if hasattr(instance, key):
                        setattr(instance, key, value)
            else:
                instance = model(**item)
                db.add(instance)

            result_objs.append(instance)

        # Commit & refresh
        db_commit(db, result_objs)

        return result_objs[0] if len(result_objs) == 1 else result_objs

    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Database operation failed: {str(e)}")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Database operation failed: {str(e)}")
        


async def delete_records(
    db: Session,
    model: Type,
    **kwargs
):
    try:
        deleted_objs = []
        instances = db.query(model).filter_by(**kwargs).all()
        if not instances:
            return []
        for instance in instances:
            deleted_objs.append(instance)
            db.delete(instance)
        db_commit(db)
        return deleted_objs
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


async def get_records(
    db: Session,
    model: Type,
    **kwargs
):
    """
    Retrieve records from the database based on optional filter conditions.
    Returns an empty dict if no records found.
    """
    try:
        instances = db.query(model).filter_by(**kwargs).all()

        return {} if not instances else instances
        # print(**instances)
        # retur/n "success"
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Database read failed: {str(e)}")