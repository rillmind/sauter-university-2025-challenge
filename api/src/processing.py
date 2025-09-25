import asyncio
from datetime import date
from typing import List, Dict, Any
import service


async def run_workflow(start_date: date, end_date: date) -> List[Dict[str, Any]]:
  """
  Orchestrates the entire workflow for the given date range, returning all data.
  """
  print("Fetching ONS resource list...")
  all_resources = await service.get_ons_resources()
  if not all_resources:
    print("Could not retrieve any resources from ONS.")
    return []

  print("Filtering for best available format...")
  resources_to_process = service.filter_resources_by_year_and_format(
    all_resources, start_date, end_date
  )

  if not resources_to_process:
    print(f"No resources found for the date range.")
    return []

  print(f"Found {len(resources_to_process)} resources. Starting parallel processing...")

  # CORREÇÃO APLICADA AQUI: O nome da função foi atualizado
  tasks = [service.process_resource(res) for res in resources_to_process]
  results = await asyncio.gather(*tasks)

  # Achatando la lista de listas de resultados em uma única lista de registros
  all_records = [record for result_list in results for record in result_list if result_list]

  print(f"Workflow complete. Processed {len(all_records)} total records.")
  return all_records