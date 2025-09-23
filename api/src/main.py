from datetime import date

from fastapi import FastAPI, HTTPException, Body
from pydantic import BaseModel, Field

import service

# --- Modelos de Dados da API ---

class DateRangeRequest(BaseModel):
  startDate: date = Field(..., example="2024-01-01", description="Data de início (YYYY-MM-DD)")
  endDate: date = Field(..., example="2024-01-10", description="Data de fim (YYYY-MM-DD)")

# --- Aplicação FastAPI ---

app = FastAPI(
  title="Pipeline de Dados ONS",
  description="Uma API para orquestrar a extração, transformação e carga de dados da ONS para o GCP.",
  version="1.0.0"
)

@app.post("/run-etl-pipeline")
def run_pipeline(date_range: DateRangeRequest = Body(...)):
  """
  Este endpoint dispara o fluxo completo de ETL:
  1. Busca os dados da ONS para o intervalo de datas.
  2. Processa e normaliza os dados anualmente.
  3. Salva cada ano como um arquivo CSV no Google Cloud Storage.
  4. Carrega cada arquivo do GCS para uma tabela no BigQuery.
  """
  try:
    # Chama o serviço que orquestra todo o fluxo
    result = service.run_full_etl_pipeline(
      start_date=date_range.startDate,
      end_date=date_range.endDate
    )
    return {
      "status": "Sucesso",
      "mensagem": "Pipeline de ETL executado com sucesso.",
      "detalhes": result
    }
  except ValueError as ve:
    # Erros de negócio (ex: data inválida, nenhum dado encontrado)
    raise HTTPException(status_code=400, detail=str(ve))
  except ConnectionError as ce:
    # Erro de conexão com a API externa
    raise HTTPException(status_code=503, detail=str(ce))
  except Exception as e:
    # Captura outros erros inesperados
    raise HTTPException(status_code=500, detail=f"Ocorreu um erro interno inesperado: {e}")

