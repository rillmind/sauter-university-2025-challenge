import os
import re
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple

import numpy as np
import pandas as pd
import requests

COLUNA_DE_DATA = "ear_data"
PADRAO_ANO_PARQUET = re.compile(r'_(\d{4})\.parquet')


def filtrar_urls_por_ano(
    urls: List[str],
    anos: range
) -> List[str]:
  padrao = re.compile(r'_(\d{4})\.parquet')
  return [u for u in urls if (m := padrao.search(u)) and int(m.group(1)) in anos]


def normalizar_e_filtrar_df_por_intervalo(df: pd.DataFrame, first_date, last_date) -> pd.DataFrame:
  if COLUNA_DE_DATA not in df.columns:
    return pd.DataFrame()
  df = df.copy()
  df[COLUNA_DE_DATA] = pd.to_datetime(df[COLUNA_DE_DATA], errors="coerce").dt.date
  df = df.dropna(subset=[COLUNA_DE_DATA])
  df = df[(df[COLUNA_DE_DATA] >= first_date) & (df[COLUNA_DE_DATA] <= last_date)]
  if df.empty:
    return df
  df = df.sort_values(by=[COLUNA_DE_DATA])
  df[COLUNA_DE_DATA] = df[COLUNA_DE_DATA].astype(str)
  df = df.replace([np.inf, -np.inf], None)
  df = df.where(pd.notna(df), None)
  return df


def extrair_ano(url: str) -> Optional[str]:
  m = PADRAO_ANO_PARQUET.search(url)
  return m.group(1) if m else None


def nome_csv(ano: Optional[str], first_date, last_date, data_ref: str) -> str:
  a = ano or "desconhecido"
  return f"ons_reservatorios_{a}_{first_date.isoformat()}_{last_date.isoformat()}_{data_ref}.csv"


def records_para_json(df: pd.DataFrame) -> List[Dict[str, Any]]:
  df = df.replace([np.inf, -np.inf], None)
  df = df.astype(object).where(pd.notna(df), None)
  return df.to_dict(orient="records")


def get_parquet_urls() -> List[str]:
  url = "https://dados.ons.org.br/api/3/action/package_show?id=61e92787-9847-4731-8b73-e878eb5bc158"
  resp = requests.get(url, timeout=60)
  resp.raise_for_status()
  recursos = resp.json().get("result", {}).get("resources", [])
  urls = sorted([r.get("url", "") for r in recursos if r.get("url", "").endswith(".parquet")])
  if not urls:
    raise ValueError("Nenhum arquivo .parquet encontrado.")
  return urls


def processar_url(url: str, first_date, last_date, diretorio_saida: str, data_ref: str) -> Optional[
  Tuple[str, int, List[Dict[str, Any]]]]:
  df = pd.read_parquet(url)
  df = normalizar_e_filtrar_df_por_intervalo(df, first_date, last_date)
  if df.empty:
    return None
  ano = extrair_ano(url)
  nome_arquivo = nome_csv(ano, first_date, last_date, data_ref)
  caminho_csv = os.path.join(diretorio_saida, nome_arquivo)
  df.to_csv(caminho_csv, index=False)
  registros = records_para_json(df)
  return caminho_csv, len(df), registros


def processar_por_ano_com_preview(
    first_date,
    last_date,
    diretorio_saida: str = "data/processed",
    preview_limit: int = 50
) -> Dict[str, Any]:
  if first_date > last_date:
    raise ValueError("firstDate não pode ser maior que lastDate.")
  os.makedirs(diretorio_saida, exist_ok=True)

  urls = get_parquet_urls()
  anos = range(first_date.year, last_date.year + 1)
  urls_filtradas = filtrar_urls_por_ano(urls, anos)
  if not urls_filtradas:
    raise ValueError("Nenhum arquivo encontrado para o intervalo solicitado.")

  data_ref = datetime.now(timezone.utc).strftime("%Y%m%d")
  caminhos_csv: List[str] = []
  preview_items: List[Dict[str, Any]] = []
  total_registros = 0

  for url in urls_filtradas:
    try:
      resultado = processar_url(url, first_date, last_date, diretorio_saida, data_ref)
      if not resultado:
        continue
      caminho_csv, qtd, registros = resultado
      caminhos_csv.append(caminho_csv)
      total_registros += qtd
      if len(preview_items) < preview_limit:
        faltam = preview_limit - len(preview_items)
        preview_items.extend(registros[:faltam])
    except Exception:
      continue

  if not caminhos_csv:
    raise ValueError("Nenhum dado disponível no intervalo após o processamento.")

  return {
    "arquivos_csv": [os.path.basename(p) for p in caminhos_csv],
    "total_registros": int(total_registros),
    "items": preview_items
  }
