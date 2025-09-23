import re
from datetime import date
from typing import List, Dict, Any

import numpy as np
import pandas as pd
import requests

# --- Constantes de Processamento ---
DATE_COLUMN = "ena_data"
TARGET_FORMAT = "CSV"
YEAR_PATTERN = re.compile(r'_(\d{4})\.(csv|parquet)', re.IGNORECASE)


def get_csv_resources(package_id: str) -> List[Dict[str, Any]]:
  """Busca todos os recursos do tipo CSV de um pacote de dados da ONS."""
  api_url = f"https://dados.ons.org.br/api/3/action/package_show?id={package_id}"
  try:
    response = requests.get(api_url, timeout=60)
    response.raise_for_status()
    data = response.json()
    if not data.get("success"):
      raise ValueError(f"Pacote '{package_id}' não encontrado.")

    all_resources = data.get("result", {}).get("resources", [])
    csv_resources = [r for r in all_resources if r.get("format", "").upper() == TARGET_FORMAT]

    if not csv_resources:
      raise ValueError(f"Nenhum recurso CSV encontrado no pacote '{package_id}'.")
    return csv_resources
  except requests.RequestException as e:
    raise ConnectionError(f"Erro ao conectar com a API da ONS: {e}")


def process_data_for_year(year: int, all_resources: List[Dict[str, Any]], start_date: date,
                          end_date: date) -> pd.DataFrame:
  """Carrega, filtra e normaliza os dados de um ano específico."""
  resources_for_year = [
    r for r in all_resources
    if (match := YEAR_PATTERN.search(r.get("url", ""))) and int(match.group(1)) == year
  ]
  if not resources_for_year:
    return pd.DataFrame()

  df_list = []
  for resource in resources_for_year:
    url = resource.get("url")
    if not url:
      continue
    try:
      df = pd.read_csv(url, sep=';', decimal=',')
      df_list.append(df)
    except Exception as e:
      print(f"Aviso: Falha ao ler o arquivo {url}. Erro: {e}")
      continue

  if not df_list:
    return pd.DataFrame()

  yearly_df = pd.concat(df_list, ignore_index=True)

  if DATE_COLUMN not in yearly_df.columns:
    return pd.DataFrame()

  # Normalização e limpeza
  yearly_df[DATE_COLUMN] = pd.to_datetime(yearly_df[DATE_COLUMN], errors="coerce").dt.date
  yearly_df.dropna(subset=[DATE_COLUMN], inplace=True)

  # Filtro pelo intervalo de datas exato
  mask = (yearly_df[DATE_COLUMN] >= start_date) & (yearly_df[DATE_COLUMN] <= end_date)
  df_filtered = yearly_df.loc[mask].copy()

  if df_filtered.empty:
    return pd.DataFrame()

  df_filtered.replace([np.inf, -np.inf], None, inplace=True)
  df_final = df_filtered.where(pd.notna(df_filtered), None)

  return df_final

