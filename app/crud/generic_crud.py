import uuid
from pathlib import Path
from bson import ObjectId
from fastapi import HTTPException, UploadFile
from sqlalchemy import func, text
from sqlalchemy.orm import Session
from typing import Type
from app.utils import convertTOString,formatDatetime
import operator

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



#---------------------------- Filter ------------------------------
async def filter_record(db: Session, model, **kwargs):
    OPERATORS = {
        "==": operator.eq,
        "!=": operator.ne,
        ">": operator.gt,
        "<": operator.lt,
        ">=": operator.ge,
        "<=": operator.le,
    }
    
    where_list = []
    for key, value in kwargs.items():
        op, fil_value = value
        op_fun = OPERATORS.get(op)

        column = getattr(model, key, None)
        if not column:
            raise ValueError(f"Invalid filter column: {key}")

        where_list.append(op_fun(column, fil_value))

    instances = db.query(model).filter(operator.and_(*where_list)).all()
    return instances


#------------------------------ SEARCH ------------------------------

def search(db: Session, model, q: str, page: int, per_page: int):
    offset = (page - 1) * per_page
    
    # ---------------- FULL TEXT SEARCH ----------------
    ts_query = func.websearch_to_tsquery('english', q)
    rank = func.ts_rank_cd(text('search_vector'), ts_query).label('rank')

    fts_q = (
        db.query(model, rank)
          .filter(text("search_vector @@ websearch_to_tsquery('english', :q)"))
          .params(q=q)
          .order_by(text("rank DESC"))
          .offset(offset)
          .limit(per_page)
    )

    results = fts_q.all()

    if results:
        instances = [row[0] for row in results]
        print("FTS_result")
        return instances

    # ---------------- TRIGRAM SEARCH (PREFIX/SUFFIX/FUZZY) ----------------
    # If FTS returns no results, fall back to trigram similarity search
    # This handles partial matches, typos, prefix, and suffix searches
    
    db.execute(text("SELECT set_limit(0.005);"))
        
    similarity = func.similarity(text('search_text'), q).label('similarity')
    
    trigram_q = (
        db.query(model, similarity)
        .filter(text("search_text % :q")) 
        .params(q=q)
        .order_by(text("similarity DESC"))
        .offset(offset)
        .limit(per_page)
    )
    
    trigram_results = trigram_q.all()
    
    if trigram_results:
        instances = [row[0] for row in trigram_results]
        print("trigram_results")
        return instances
    
    
    # ---------------- ILIKE SEARCH (LAST RESORT) ----------------
    # If both FTS and trigram fail, try basic pattern matching
    ilike_pattern = f"%{q}%"
    
    ilike_q = (
        db.query(model)
          .filter(text("search_text ILIKE :pattern"))
          .params(pattern=ilike_pattern)
          .offset(offset)
          .limit(per_page)
    )
    
    ilike_results = ilike_q.all()
    print("like_result")
    return ilike_results if ilike_results else []  

   
# --------------------- SAVE ONE IMAGE ---------------------

async def save_image(image: UploadFile, sub_static_dir: str):
    if not image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    static_dir = Path(f"app/static/{sub_static_dir}")
    static_dir.mkdir(parents=True, exist_ok=True)

    extension = image.filename.split(".")[-1]
    filename = f"{uuid.uuid4()}.{extension}"
    file_path = static_dir / filename

    content = await image.read()  
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


#----------------------------------------------------------------------------------------------


async def insert_record_mongo(collection,data):
    
    result = await collection.insert_one(data)
    inserted_doc = await collection.find_one({"_id": result.inserted_id})
    inserted_doc["id"] = convertTOString(inserted_doc["_id"])
    inserted_doc["created_at"] = formatDatetime(inserted_doc["created_at"])
    return inserted_doc
    


async def update_record_mongo(id: str, collection, update_data: dict):
    try:
        object_id = ObjectId(id)
    except Exception:
        return {"updated": False, "error": "Invalid ID format"}

    update_data["created_at"] = formatDatetime(update_data["created_at"])


    result = await collection.update_one(
        {"_id": object_id}, {"$set": update_data}
    )

    if result.matched_count == 0:
        return {"updated": False, "error": "Document not found"}

    updated_doc = await collection.find_one({"_id": object_id})
    if updated_doc:
        updated_doc["id"] = str(updated_doc.pop("_id"))

    return {
        "updated": True,
        "modified_count": result.modified_count,
        "data": updated_doc
    }


async def delete_record_mongo(id : str,collection):
    
    try:
        object_id = ObjectId(id)
    except Exception:
        return {"deleted": False, "error": "Invalid ID format"}
    
    result = await collection.delete_one({"_id": object_id})
    
    return {
        "deleted": result.deleted_count == 1,
        "deleted_count": result.deleted_count
    }
    

async def get_record_mongo(id : str,collection):
    
    try:
        object_id = ObjectId(id)
    except Exception:
        return {"deleted": False, "error": "Invalid ID format"}
    
    result = await collection.find_one({"_id": object_id})
    
    return result

