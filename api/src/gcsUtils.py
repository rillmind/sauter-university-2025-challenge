import os
import pandas as pd
from google.cloud import storage

GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME")
if not GCS_BUCKET_NAME:
    raise ValueError("A variável de ambiente GCS_BUCKET_NAME não foi definida.")

def upload_df_as_csv_to_gcs(df: pd.DataFrame, gcs_filename: str) -> str:
  """
  Converte um DataFrame para CSV em memória e faz o upload para o GCS.

  Args:
      df: O DataFrame do pandas para ser salvo.
      gcs_filename: O caminho completo do arquivo no bucket (ex: 'dados/meu_arquivo.csv').

  Returns:
      A URI do GCS para o arquivo criado (ex: 'gs://seu-bucket-aqui/dados/meu_arquivo.csv').
  """
  client = storage.Client()
  bucket = client.bucket(GCS_BUCKET_NAME)
  blob = bucket.blob(gcs_filename)

  # Converte o DataFrame para uma string CSV
  csv_data = df.to_csv(index=False, sep=';', decimal=',')

  # Faz o upload da string para o GCS
  blob.upload_from_string(csv_data, content_type='text/csv')

  gcs_uri = f"gs://{GCS_BUCKET_NAME}/{gcs_filename}"
  print(f"Arquivo enviado com sucesso para: {gcs_uri}")
  return gcs_uri
