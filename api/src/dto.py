from pydantic import BaseModel
from datetime import date
from typing import List, Dict, Any

class DateRangeRequest(BaseModel):
    start_date: date
    end_date: date

class ProcessResponse(BaseModel):
    message: str
    total_records: int
    total_pages: int
    current_page: int
    page_size: int
    data: List[Dict[str, Any]]