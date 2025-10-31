from fastapi import APIRouter,Request,Depends
from sqlalchemy.orm import Session
from typing import List
from app.schemas.general_query_schema import GeneralQueryResponseSchema,UserQuerySchema
from app.crud import generalQuery
from app.core.dependency import get_db


router = APIRouter(prefix="/GeneralQuery", tags=["GeneralQuery"])


# User posts a new query
@router.post("/", response_model=UserQuerySchema)
async def create_query(query: UserQuerySchema,request: Request,db: Session = Depends(get_db)):
    result = await generalQuery.create_query(query,request,db)
    return result

# Admin responds to a query
@router.put("/{query_id}/response", response_model=UserQuerySchema)
async def respond_query(query_id: str, response: GeneralQueryResponseSchema):
    result = await generalQuery.respond_query(query_id,response)
    return result

# Get all general queries
@router.get("/", response_model=List[UserQuerySchema])
async def get_all_queries():
    result = await generalQuery.get_all_queries()
    return result