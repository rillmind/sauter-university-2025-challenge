import asyncio
import io
import os
from datetime import date
from typing import List, Dict, Any, Hashable

import httpx
import pandas as pd
from google.cloud import bigquery

# Configurações Google Cloud
ID_TABELA = os.getenv("BQ_TABLE_ID")
ID_DATASET = os.getenv("BQ_DATASET_ID")
ID_PROJETO = os.getenv("GCP_PROJECT_ID")
NOME_BUCKET = os.getenv("GCS_BUCKET_NAME")

# Configurações ONS
ID_PACOTE = "148e56a4-5a21-4bf2-9cd7-7f89bc4ed71c"
URL_PACOTE_ONS = f"https://dados.ons.org.br/api/3/action/package_show?id={ID_PACOTE}"
URL_DOWNLOAD_RECURSO_ONS = f"https://dados.ons.org.br/dataset/{ID_PACOTE}/resource/"

bq_client = bigquery.Client(project=ID_PROJETO, location="us-central1") if ID_PROJETO else None


async def obter_recursos_ons() -> List[Dict[str, Any]]:
  """Busca a lista de todos os recursos de dados disponíveis no pacote da ONS."""
  try:
    async with httpx.AsyncClient(timeout=30.0) as client:
      response = await client.get(URL_PACOTE_ONS)
      response.raise_for_status()
      dados_pacote = response.json()
      return dados_pacote.get("result", {}).get("resources", [])
  except httpx.RequestError as e:
    print(f"Erro ao buscar os dados do pacote ONS: {e}")
    return []


def filtrar_recursos_por_ano_e_formato(
    recursos: List[Dict[str, Any]], data_inicio_req: date, data_fim_req: date
) -> List[Dict[str, Any]]:
  """Encontra o melhor formato disponível (dando preferência a Parquet) para cada ano solicitado."""
  melhores_recursos_por_ano = {}
  anos_solicitados = set(range(data_inicio_req.year, data_fim_req.year + 1))
  for rec in recursos:
    try:
      url = rec.get("url", "")
      tipo_formato = rec.get("format", "").upper()
      if tipo_formato not in ["PARQUET", "CSV"]:
        continue

      nome_arquivo = url.split("/")[-1]
      ano_str = nome_arquivo.replace(".csv", "").replace(".parquet", "").split("_")[-1]

      if not ano_str.isdigit():
        continue

      ano_recurso = int(ano_str if len(ano_str) == 4 else ano_str[:4])

      if ano_recurso in anos_solicitados:
        if ano_recurso not in melhores_recursos_por_ano or tipo_formato == "PARQUET":
          rec['ano'] = ano_recurso
          melhores_recursos_por_ano[ano_recurso] = rec

    except (ValueError, IndexError):
      continue

  lista_final = list(melhores_recursos_por_ano.values())
  print(f"DEBUG: Encontrados {len(lista_final)} recursos ideais para processar.")
  return lista_final


def _buscar_e_processar_recurso(recurso: Dict[str, Any]) -> list[Any] | list[dict[Hashable, Any]]:
  """
  Processa um único recurso: baixa, converte para Parquet no GCS e retorna os dados.
  """
  url_download = URL_DOWNLOAD_RECURSO_ONS + recurso.get("id") + "/download"
  print(f"  -> Buscando {recurso.get('name')} ({recurso.get('format')})...")

  if not url_download:
    return []

  try:
    nome_arquivo = recurso.get("name")
    formato_arquivo = recurso.get("format", "").upper()
    print(f"  -> Processando {nome_arquivo} ({formato_arquivo})...")

    with httpx.Client() as client:
        response = client.get(url_download, follow_redirects=True, timeout=60.0)
        response.raise_for_status()
        content_bytes = response.content

    if formato_arquivo == "CSV":
      df = pd.read_csv(io.BytesIO(content_bytes), sep=';', header=1, encoding='latin-1')
    elif formato_arquivo == "PARQUET":
      df = pd.read_parquet(io.BytesIO(content_bytes))
    else:
      return []

    if NOME_BUCKET:
      try:
        data_ingestao = date.today().strftime('%Y-%m-%d')
        nome_original = url_download.split("/")[-1]
        nome_base = os.path.splitext(nome_original)[0]
        caminho_gcs = f"gs://{NOME_BUCKET}/dt={data_ingestao}/{nome_base}.parquet"

        print("  -> Convertendo todas as colunas para string para o arquivo Parquet...")
        df_para_parquet = df.astype(str)

        print(f"  -> Fazendo upload para {caminho_gcs}...")
        df_para_parquet.to_parquet(caminho_gcs, index=False)
        print(f"  SUCESSO! Arquivo Parquet (com strings) enviado para o GCS.")

      except Exception as e:
        print(f"  [!!!] FALHA NO UPLOAD PARA O GCS: {e}")
    else:
      print("  -> AVISO: NOME_BUCKET_GCS não configurado. Upload ignorado.")

    df = df.where(pd.notna(df), None)
    print(f"  SUCESSO! Processados {len(df)} registros de {nome_arquivo}")
    return df.to_dict(orient='records')

  except Exception as e:
    print(f"  [!!!] ERRO CRÍTICO durante o processamento: {e}")
    return []

async def processar_recurso(recurso: Dict[str, Any]) -> List[Dict[str, Any]]:
  """Função assíncrona que encapsula o processamento para rodar em uma thread separada."""
  return await asyncio.to_thread(_buscar_e_processar_recurso, recurso)


async def consultar_dados_por_intervalo(
    data_inicio: date, data_fim: date
) -> List[Dict[str, Any]]:
  """
  Executa uma consulta no BigQuery para buscar registros num intervalo de datas.
  """
  if not bq_client:
    print("Erro: Cliente do BigQuery não foi inicializado. Verifique a variável de ambiente GCP_PROJECT_ID.")
    return []

  query = f"""
    SELECT
      *
    FROM
      `{ID_PROJETO}.{ID_DATASET}.{ID_TABELA}`
    WHERE
      ena_data >= @data_inicio
      AND ena_data <= @data_fim
    ORDER BY
      ena_data DESC
    """
  job_config = bigquery.QueryJobConfig(
    query_parameters=[
      bigquery.ScalarQueryParameter("data_inicio", "DATE", data_inicio),
      bigquery.ScalarQueryParameter("data_fim", "DATE", data_fim),
    ]
  )
  try:
    print(f"Executando a consulta no BigQuery no intervalo de {data_inicio} a {data_fim}...")
    # A API do cliente Python do BigQuery é síncrona, então a executamos em uma thread separada
    # para não bloquear o loop de eventos do asyncio.
    query_job = await asyncio.to_thread(bq_client.query, query, job_config=job_config)

    resultados = await asyncio.to_thread(lambda: [dict(row) for row in query_job.result()])

    print(f"Consulta concluída. {len(resultados)} registros encontrados.")
    return resultados
  except Exception as e:
    print(f"Erro ao consultar o BigQuery: {e}")
    return []
