# main.py
from fastapi import FastAPI, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from pydantic import BaseModel
from dummy.db import SessionLocal
from dummy.models import Hotel
from sqlalchemy import or_, and_

app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class HotelOut(BaseModel):
    id: int
    name: str
    city: str
    description: str | None
    stars: int | None

    class Config:
        orm_mode = True

@app.get("/search", response_model=list[HotelOut])
def search_hotels(q: str = Query(..., min_length=1), page:int=1, per_page:int=10, db: Session = Depends(get_db)):
    offset = (page-1) * per_page

    # 1) Full text search query
    ts_query = func.websearch_to_tsquery('english', q)

    # Use ts_rank_cd to compute rank
    rank = func.ts_rank_cd(text('hotel.search_vector'), ts_query).label('rank')

    # Build query: FTS first
    fts_q = (
        db.query(Hotel, rank)
          .filter(Hotel.search_vector.op('@@')(ts_query))
          .params(q=q)
          .order_by(text("rank DESC"))
          .offset(offset)
          .limit(per_page)
    )

    results = fts_q.all()
    if results:
        # unpack Hotel from tuples (Hotel, rank)
        hotels = [row[0] for row in results]
        return hotels

    # 2) If no FTS hits, fallback to trigram similarity on name and city
    # similarity(name, :q) and similarity(city, :q)
    sim_expr = func.greatest(func.similarity(Hotel.name, q), func.similarity(Hotel.city, q)).label('sim')
    fallback_q = (
        db.query(Hotel)
          .filter(
              or_(
                  func.similarity(Hotel.name, q) > 0.2,
                  func.similarity(Hotel.city, q) > 0.2
              )
          )          
          .order_by(text("GREATEST(similarity(name, :q), similarity(city, :q)) DESC")).params(q=q)
          .offset(offset)
          .limit(per_page)
    )
    hotels = fallback_q.all()
    return hotels


@app.get("/autocomplete")
def autocomplete(q: str = Query(..., min_length=1), limit: int = 8, db: Session = Depends(get_db)):
    pattern = q + '%'
    results = db.query(Hotel).filter(Hotel.name.ilike(pattern)).order_by(func.length(Hotel.name)).limit(limit).all()
    return [{"id": h.id, "name": h.name, "city": h.city} for h in results]
