import os
import unittest
from datetime import date, datetime
from unittest.mock import patch, MagicMock

import pandas as pd
from freezegun import freeze_time

from service import (
  filtrar_urls_por_ano,
  extrair_ano,
  nome_csv,
  records_para_json,
  normalizar_e_filtrar_df_por_intervalo,
  get_parquet_urls,
  processar_url,
  processar_por_ano_com_preview
)


class TestService(unittest.TestCase):

  def test_filtrar_urls_por_ano(self):
    urls = [
      "http://example.com/dados_2022.parquet",
      "http://example.com/dados_2023.parquet",
      "http://example.com/dados_2024.parquet"
    ]
    anos = range(2023, 2025)
    resultado = filtrar_urls_por_ano(urls, anos)
    self.assertEqual(len(resultado), 2)
    self.assertIn("http://example.com/dados_2023.parquet", resultado)
    self.assertIn("http://example.com/dados_2024.parquet", resultado)

  def test_extrair_ano(self):
    url = "http://example.com/dados_2023.parquet"
    ano = extrair_ano(url)
    self.assertEqual(ano, "2023")

  def test_extrair_ano_sem_ano(self):
    url = "http://example.com/dados.parquet"
    ano = extrair_ano(url)
    self.assertIsNone(ano)

  @freeze_time("2023-10-26")
  def test_nome_csv(self):
    first_date = date(2023, 1, 1)
    last_date = date(2023, 12, 31)
    data_ref = datetime.utcnow().strftime("%Y%m%d")
    nome = nome_csv("2023", first_date, last_date, data_ref)
    self.assertEqual(nome, "ons_reservatorios_2023_2023-01-01_2023-12-31_20231026.csv")

  def test_records_para_json(self):
    df = pd.DataFrame({
      "col1": [1, 2],
      "col2": ["A", "B"]
    })
    resultado = records_para_json(df)
    self.assertEqual(resultado, [{"col1": 1, "col2": "A"}, {"col1": 2, "col2": "B"}])

  def test_normalizar_e_filtrar_df_por_intervalo(self):
    df = pd.DataFrame({
      "ear_data": ["2023-01-01", "2023-01-15", "2023-02-01"],
      "valor": [10, 20, 30]
    })
    first_date = date(2023, 1, 10)
    last_date = date(2023, 1, 20)
    resultado = normalizar_e_filtrar_df_por_intervalo(df, first_date, last_date)
    self.assertEqual(len(resultado), 1)
    self.assertEqual(resultado.iloc[0]["valor"], 20)

  @patch("app.service.requests.get")
  def test_get_parquet_urls(self, mock_get):
    mock_response = MagicMock()
    mock_response.json.return_value = {
      "result": {
        "resources": [
          {"url": "http://example.com/dados_2023.parquet"},
          {"url": "http://example.com/dados_2024.parquet"}
        ]
      }
    }
    mock_get.return_value = mock_response
    urls = get_parquet_urls()
    self.assertEqual(len(urls), 2)
    self.assertIn("http://example.com/dados_2023.parquet", urls)

  @patch("app.service.pd.read_parquet")
  @patch("app.service.os.path.join")
  @patch("app.service.pd.DataFrame.to_csv")
  def test_processar_url(self, mock_to_csv, mock_join, mock_read_parquet):
    mock_df = pd.DataFrame({
      "ear_data": ["2023-01-15"],
      "valor": [20]
    })
    mock_read_parquet.return_value = mock_df
    mock_join.return_value = "/fake/path/ons_reservatorios_2023_2023-01-01_2023-01-31_20231026.csv"

    first_date = date(2023, 1, 1)
    last_date = date(2023, 1, 31)
    data_ref = "20231026"
    resultado = processar_url("http://example.com/dados_2023.parquet", first_date, last_date, "/fake/path",
                              data_ref)

    self.assertIsNotNone(resultado)
    self.assertEqual(resultado[0], "/fake/path/ons_reservatorios_2023_2023-01-01_2023-01-31_20231026.csv")
    self.assertEqual(resultado[1], 1)
    self.assertEqual(len(resultado[2]), 1)
    mock_to_csv.assert_called_once()

  @patch("app.service.get_parquet_urls")
  @patch("app.service.processar_url")
  @patch("app.service.os.makedirs")
  def test_processar_por_ano_com_preview(self, mock_makedirs, mock_processar_url, mock_get_parquet_urls):
    mock_get_parquet_urls.return_value = ["http://example.com/dados_2023.parquet"]
    mock_processar_url.return_value = (
    "/fake/path/ons_reservatorios_2023_2023-01-01_2023-01-31_20231026.csv", 1, [{"valor": 20}])

    first_date = date(2023, 1, 1)
    last_date = date(2023, 1, 31)
    resultado = processar_por_ano_com_preview(first_date, last_date)

    self.assertIsNotNone(resultado)
    self.assertEqual(len(resultado["arquivos_csv"]), 1)
    self.assertEqual(resultado["total_registros"], 1)
    self.assertEqual(len(resultado["items"]), 1)
    mock_makedirs.assert_called_once()
