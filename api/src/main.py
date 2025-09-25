import math
from fastapi import FastAPI, HTTPException, status, Query
from dto import DateRangeRequest, ProcessResponse
from processing import run_workflow
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()


@app.get("/health", status_code=status.HTTP_200_OK, tags=["Monitoring"])
def health_check():
  """Simple health check endpoint."""
  return {"status": "ok"}


@app.post("/process", response_model=ProcessResponse)
async def process_files_endpoint(
    request: DateRangeRequest,
    page: int = Query(1, description="Page number to retrieve", ge=1),
    size: int = Query(20, description="Number of items per page", ge=1),
) -> ProcessResponse:
  """
  Triggers a data processing workflow and returns the data paginated in the response body.
  """
  if request.start_date > request.end_date:
    raise HTTPException(
      status_code=status.HTTP_400_BAD_REQUEST,
      detail="start_date cannot be after end_date."
    )

  all_records = await run_workflow(request.start_date, request.end_date)

  total_records = len(all_records)
  total_pages = math.ceil(total_records / size) if total_records > 0 else 0

  start_index = (page - 1) * size
  end_index = start_index + size
  paginated_data = all_records[start_index:end_index]

  if not all_records:
    message = "Workflow finished, but no data was processed."
  else:
    message = f"Successfully processed {total_records} records."

  return ProcessResponse(
    message=message,
    total_records=total_records,
    total_pages=total_pages,
    current_page=page,
    page_size=size,
    data=paginated_data,
  )