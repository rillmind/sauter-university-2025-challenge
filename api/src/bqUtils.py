import os
from google.cloud import bigquery

GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")
BIGQUERY_DATASET = os.getenv("BIGQUERY_DATASET")
BIGQUERY_TABLE = os.getenv("BIGQUERY_TABLE")

if not all([GCP_PROJECT_ID, BIGQUERY_DATASET, BIGQUERY_TABLE]):
    raise ValueError("Uma ou mais variáveis de ambiente do BigQuery não foram definidas.")

def load_gcs_csv_to_bigquery(gcs_uri: str) -> str:
  """
  Inicia um job no BigQuery para carregar um arquivo CSV do GCS para uma tabela.

  Args:
      gcs_uri: A URI do arquivo no GCS (ex: 'gs://bucket/arquivo.csv').

  Returns:
      O ID do job do BigQuery que foi iniciado.
  """
  client = bigquery.Client(project=GCP_PROJECT_ID)
  table_id = f"{GCP_PROJECT_ID}.{BIGQUERY_DATASET}.{BIGQUERY_TABLE}"

  job_config = bigquery.LoadJobConfig(
    source_format=bigquery.SourceFormat.CSV,
    skip_leading_rows=1,  # Pula o cabeçalho
    autodetect=True,  # Detecta o schema automaticamente
    write_disposition=bigquery.WriteDisposition.WRITE_APPEND,  # Adiciona os dados à tabela
  )

  load_job = client.load_table_from_uri(
    gcs_uri, table_id, job_config=job_config
  )

  load_job.result()  # Espera o job ser concluído

  print(f"Job do BigQuery '{load_job.job_id}' concluído. Dados carregados em {table_id}.")
  return load_job.job_id
