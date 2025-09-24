import os
import httpx
import asyncio
from datetime import date
from typing import List, Dict, Any
import pandas as pd

GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME")

PACKAGE_ID = "148e56a4-5a21-4bf2-9cd7-7f89bc4ed71c"
ONS_PACKAGE_URL = f"https://dados.ons.org.br/api/3/action/package_show?id={PACKAGE_ID}"
ONS_DOWNLOAD_RESOURCE_URL = f"https://dados.ons.org.br/dataset/{PACKAGE_ID}/resource/"


async def get_ons_resources() -> List[Dict[str, Any]]:
  """Fetches the list of all available data resources from the ONS package API."""
  try:
    async with httpx.AsyncClient(timeout=30.0) as client:
      response = await client.get(ONS_PACKAGE_URL)
      response.raise_for_status()
      package_data = response.json()
      return package_data.get("result", {}).get("resources", [])
  except httpx.RequestError as e:
    print(f"Error fetching ONS package data: {e}")
    return []


def filter_resources_by_year_and_format(
    resources: List[Dict[str, Any]], start_date_req: date, end_date_req: date
) -> List[Dict[str, Any]]:
  """Finds the best available format (preferring Parquet) for each requested year."""
  best_resources_by_year = {}
  requested_years = set(range(start_date_req.year, end_date_req.year + 1))
  for res in resources:
    try:
      url = res.get("url", "")
      format_type = res.get("format", "").upper()
      if format_type not in ["PARQUET", "CSV"]:
        continue
      filename = url.split("/")[-1]
      year_str = filename.replace(".csv", "").replace(".parquet", "").split("_")[-1]
      if not year_str.isdigit():
        continue
      year_str = (
        year_str
        if len(year_str) == 4
        else year_str[:4] + year_str[4:6] + year_str[6:8]
      )
      resource_year = int(year_str)
      if resource_year in requested_years:
        if resource_year not in best_resources_by_year or format_type == "PARQUET":
          res['year'] = resource_year
          best_resources_by_year[resource_year] = res
    except (ValueError, IndexError):
      continue
  final_list = list(best_resources_by_year.values())
  print(f"DEBUG: Found {len(final_list)} optimal resources to process.")
  return final_list


def _fetch_and_process_resource(resource: Dict[str, Any]) -> List[Dict[str, Any]]:
  """
  Processes data, uploads it as Parquet to GCS, and returns data as a list of dicts.
  """
  download_url = ONS_DOWNLOAD_RESOURCE_URL + resource.get("id") + "/download"
  print(download_url)
  print(
    f"  -> Fetching {resource.get('name')} ({resource.get('format')})..."
  )
  if not download_url:
    return []

  try:
    print(f"  -> Processing {download_url}...")
    file_format = resource.get("format", "").upper()

    if file_format == "CSV":
      df = pd.read_csv(download_url, sep=';', header=1, encoding='latin-1')
    elif file_format == "PARQUET":
      df = pd.read_parquet(download_url)
    else:
      return []

    if GCS_BUCKET_NAME:
      try:
        ingestion_date_str = date.today().strftime('%Y-%m-%d')
        original_filename = download_url.split("/")[-1]
        base_name = os.path.splitext(original_filename)[0]
        gcs_path = f"gs://{GCS_BUCKET_NAME}/dt={ingestion_date_str}/{base_name}.parquet"

        print("  -> Converting dataframe to string types for Parquet file...")
        df_for_parquet = df.astype(str)

        print(f"  -> Uploading to {gcs_path}...")
        df_for_parquet.to_parquet(gcs_path, index=False)
        print(f"  SUCCESS! Uploaded string-typed parquet to GCS.")

      except Exception as e:
        print(f"  [!!!] GCS UPLOAD FAILED: {e}")
    else:
      print("  -> WARNING: GCS_BUCKET_NAME not set. Skipping upload.")

    df = df.where(pd.notna(df), None)
    print(f"  SUCCESS! Processed {len(df)} records from {download_url}")
    return df.to_dict(orient='records')

  except Exception as e:
    print(f"  [!!!] CRITICAL ERROR during processing: {e}")
    import traceback
    traceback.print_exc()
    return []


async def process_resource(resource: Dict[str, Any]) -> List[Dict[str, Any]]:
  """Async wrapper for the data processing function."""
  return await asyncio.to_thread(_fetch_and_process_resource, resource)