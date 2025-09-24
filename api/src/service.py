import os
import httpx
import polars as pl
from datetime import date
from typing import List, Dict, Any

DESTINATION_BUCKET_NAME = os.getenv("DESTINATION_GCS_BUCKET")

ONS_PACKAGE_ID = "148e56a4-5a21-4bf2-9cd7-7f89bc4ed71c"
ONS_PACKAGE_URL = f"https://dados.ons.org.br/api/3/action/package_show?id={ONS_PACKAGE_ID}"
ONS_RESOURCE_URL = "https://dados.ons.org.br/api/3/action/datastore_search"

async def get_ons_resources() -> List[Dict[str, Any]]:
  """
  Fetches the list of all available data resources from the ONS package API.
  """
  try:
    async with httpx.AsyncClient(timeout=30.0) as client:
      response = await client.get(ONS_PACKAGE_URL)
      response.raise_for_status()
      package_data = response.json()
      return package_data.get("result", {}).get("resources", [])
  except httpx.RequestError as e:
    print(f"Error fetching ONS package data: {e}")
    return []


def filter_resources_by_date(
    resources: List[Dict[str, Any]], start_date: date, end_date: date
) -> List[Dict[str, Any]]:
  """
  Filters the list of resources to include only those within the date range.
  The date is parsed from the resource name (e.g., 'ge-cv-YYYY-MM-DD').
  """
  filtered = []
  for res in resources:
    try:
      date_str = res["name"].split("-")[-3:]
      res_date = date.fromisoformat("-".join(date_str))
      if start_date <= res_date <= end_date:
        filtered.append(res)
    except (ValueError, IndexError):
      continue
  return filtered


async def process_and_upload_resource(resource: Dict[str, Any]) -> str:
  """
  Downloads data for a single resource, converts all columns to string,
  and uploads it as a Parquet file to GCS.
  """
  resource_id = resource.get("id")
  if not resource_id:
    return ""

  try:
    async with httpx.AsyncClient(timeout=120.0) as client:
      initial_resp = await client.get(ONS_RESOURCE_URL, params={"resource_id": resource_id, "limit": 1})
      initial_resp.raise_for_status()
      total = initial_resp.json().get("result", {}).get("total", 0)

      if total == 0:
        print(f"No data found for resource {resource_id}")
        return ""

      # Fetch all records
      all_data_resp = await client.get(ONS_RESOURCE_URL, params={"resource_id": resource_id, "limit": total})
      all_data_resp.raise_for_status()
      records = all_data_resp.json().get("result", {}).get("records", [])

    df = pl.DataFrame(records)

    df = df.with_columns([pl.all().cast(pl.Utf8)])

    file_name = f"{resource['name']}.parquet"
    gcs_parquet_path = f"gs://{DESTINATION_BUCKET_NAME}/processed/{file_name}"

    print(f"Uploading {file_name} to {gcs_parquet_path}...")
    df.write_parquet(gcs_parquet_path)

    return gcs_parquet_path

  except Exception as e:
    print(f"Error processing resource {resource_id}: {e}")
    return ""
