from pydantic import BaseModel
from datetime import date
from typing import List

class DateRangeRequest(BaseModel):
    """Defines the structure for the incoming POST request body."""
    start_date: date
    end_date: date

class ProcessResponse(BaseModel):
    """Defines the final structure of the API response."""
    message: str
    files_uploaded: List[str]
