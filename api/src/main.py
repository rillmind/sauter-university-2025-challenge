# app/main.py

from fastapi import FastAPI, HTTPException, status
from dto import DateRangeRequest, ProcessResponse
from processing import run_workflow

app = FastAPI()


@app.get("/health", status_code=status.HTTP_200_OK, tags=["Monitoring"])
def health_check():
  """Simple health check endpoint."""
  return {"status": "ok"}


@app.post(
  "/process",
  response_model=ProcessResponse,
  tags=["Processing"],
  summary="Fetch ONS data and upload to GCS"
)
async def process_files_endpoint(request: DateRangeRequest) -> ProcessResponse:
  """
  Triggers a data processing workflow for a given date range:
  - Fetches a list of data resources from the ONS API.
  - Filters them by the provided date range.
  - Downloads, transforms (all columns to string), and uploads each as a Parquet file to GCS.
  """
  if request.start_date > request.end_date:
    raise HTTPException(
      status_code=status.HTTP_400_BAD_REQUEST,
      detail="start_date cannot be after end_date."
    )

  uploaded_files = await run_workflow(request.start_date, request.end_date)

  if not uploaded_files:
    message = "Workflow finished, but no new files were uploaded."
  else:
    message = f"Successfully processed and uploaded {len(uploaded_files)} files."

  return ProcessResponse(
    message=message,
    files_uploaded=uploaded_files
  )
