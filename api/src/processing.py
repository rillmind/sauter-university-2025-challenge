import asyncio
from datetime import date
from typing import List
import service


async def run_workflow(start_date: date, end_date: date) -> List[str]:
  """
  Orchestrates the entire workflow for the given date range.
  1. Fetches all resources from ONS API.
  2. Filters resources based on the date range.
  3. Processes and uploads the data for each resource in parallel.
  """
  print("Fetching ONS resource list...")
  all_resources = await service.get_ons_resources()
  if not all_resources:
    print("Could not retrieve any resources from ONS.")
    return []

  print(f"Found {len(all_resources)} total resources. Filtering for date range...")
  resources_to_process = service.filter_resources_by_date(all_resources, start_date, end_date)

  if not resources_to_process:
    print(f"No resources found within the date range {start_date} to {end_date}.")
    return []

  print(f"Found {len(resources_to_process)} resources to process. Starting parallel upload...")

  tasks = [service.process_and_upload_resource(res) for res in resources_to_process]
  results = await asyncio.gather(*tasks)

  uploaded_files = [path for path in results if path]

  print(f"Workflow complete. Uploaded {len(uploaded_files)} files.")
  return uploaded_files
