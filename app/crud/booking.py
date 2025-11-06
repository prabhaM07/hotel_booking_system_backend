from datetime import date
from typing import List
from requests import Session

#---------------------------- Filter ------------------------------

async def whole_filter(db : Session, room_price : int,floor_no : int ,room_type_name : List[str],ratings : int,features : List[str],bet_type_names : List[str] ,check_in : date,check_out : date):
    pass