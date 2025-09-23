import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from main import app


class TestMain(unittest.TestCase):

  def setUp(self):
    self.client = TestClient(app)

  @patch("src.main.processar_por_ano_com_preview")
  def test_processar_sucesso(self, mock_processar):
    mock_processar.return_value = {
      "arquivos_csv": ["test.csv"],
      "total_registros": 1,
      "items": [{"col1": "val1"}]
    }
    response = self.client.post("/processar", json={"firstDate": "2023-01-01", "lastDate": "2023-01-31"})
    self.assertEqual(response.status_code, 200)
    data = response.json()
    self.assertEqual(data["mensagem"], "Processamento concluído com sucesso.")
    self.assertEqual(data["arquivos_csv"], ["test.csv"])
    self.assertEqual(data["preview"]["total_items"], 1)

  @patch("src.main.processar_por_ano_com_preview")
  def test_processar_value_error(self, mock_processar):
    mock_processar.side_effect = ValueError("Erro de valor")
    response = self.client.post("/processar", json={"firstDate": "2023-01-01", "lastDate": "2023-01-31"})
    self.assertEqual(response.status_code, 400)
    self.assertEqual(response.json()["detail"], "Erro de valor")

  @patch("src.main.processar_por_ano_com_preview")
  def test_processar_exception(self, mock_processar):
    mock_processar.side_effect = Exception("Erro geral")
    response = self.client.post("/processar", json={"firstDate": "2023-01-01", "lastDate": "2023-01-31"})
    self.assertEqual(response.status_code, 500)
    self.assertEqual(response.json()["detail"], "Falha ao processar: Erro geral")
