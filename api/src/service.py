from datetime import date, datetime
from typing import Dict, Any

import processing
import gcsUtils
import bqUtils

# --- Constantes do Serviço ---
PACKAGE_ID = "148e56a4-5a21-4bf2-9cd7-7f89bc4ed71c"  # Pacote de dados a ser usado


def run_full_etl_pipeline(start_date: date, end_date: date) -> Dict[str, Any]:
  """
  Executa o pipeline completo de ETL: busca, processa, salva no GCS e carrega no BigQuery.
  """
  if start_date > end_date:
    raise ValueError("A data de início não pode ser maior que a data de fim.")

  # 1. Busca a lista de todos os arquivos CSV uma única vez
  all_resources = processing.get_csv_resources(PACKAGE_ID)

  # 2. Itera sobre cada ano no intervalo solicitado
  year_range = range(start_date.year, end_date.year + 1)

  results = {
    "arquivos_criados_gcs": [],
    "jobs_bigquery_concluidos": []
  }
  data_processed = False

  for year in year_range:
    print(f"--- Processando dados para o ano: {year} ---")

    # 3. Processa os dados para o ano
    df_year = processing.process_data_for_year(year, all_resources, start_date, end_date)

    if df_year.empty:
      print(f"Nenhum dado encontrado para {year} no intervalo especificado.")
      continue

    data_processed = True

    # 4. Envia o arquivo CSV tratado para o GCS
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    gcs_filename = f"dados_tratados/ena_diario_{year}_{timestamp}.csv"
    gcs_uri = gcsUtils.upload_df_as_csv_to_gcs(df_year, gcs_filename)
    results["arquivos_criados_gcs"].append(gcs_uri)

    # 5. Carrega o arquivo do GCS para o BigQuery
    bq_job_id = bqUtils.load_gcs_csv_to_bigquery(gcs_uri)
    results["jobs_bigquery_concluidos"].append(bq_job_id)

  if not data_processed:
    raise ValueError("Nenhum dado encontrado para o intervalo de datas solicitado.")

  return results

