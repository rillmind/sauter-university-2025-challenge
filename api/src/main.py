import math
from datetime import date

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, status, Query

from dto import RequisicaoIntervaloDatas, RespostaProcessamento
from processing import executar_fluxo
from service import consultar_dados_por_intervalo

load_dotenv()

app = FastAPI()


@app.get("/health", status_code=status.HTTP_200_OK, tags=["Monitoramento"])
def verificar_saude():
  """Endpoint simples para verificar se a API está no ar."""
  return {"status": "ok"}


@app.get("/consultar", response_model=RespostaProcessamento, tags=["Consulta BigQuery"])
async def endpoint_consultar_bigquery(
    data_inicio: date = Query(..., description="Data de início no formato AAAA-MM-DD"),
    data_fim: date = Query(..., description="Data de fim no formato AAAA-MM-DD"),
    pagina: int = Query(1, description="Número da página a ser retornada", ge=1),
    tamanho: int = Query(20, description="Quantidade de itens por página", ge=1),
) -> RespostaProcessamento:
  """
  Consulta o BigQuery por um intervalo de datas e retorna os resultados paginados.
  """
  if data_inicio > data_fim:
    raise HTTPException(
      status_code=status.HTTP_400_BAD_REQUEST,
      detail="A data de início não pode ser posterior à data de fim."
    )

  todos_os_registros = await consultar_dados_por_intervalo(data_inicio, data_fim)

  total_de_registros = len(todos_os_registros)
  total_de_paginas = math.ceil(total_de_registros / tamanho) if total_de_registros > 0 else 0
  indice_inicio = (pagina - 1) * tamanho
  indice_fim = indice_inicio + tamanho
  dados_paginados = todos_os_registros[indice_inicio:indice_fim]

  if not todos_os_registros:
    mensagem = "Nenhum dado encontrado no BigQuery para o período especificado."
  else:
    mensagem = f"Consulta retornou {total_de_registros} registros com sucesso."

  return RespostaProcessamento(
    mensagem=mensagem,
    total_registros=total_de_registros,
    total_paginas=total_de_paginas,
    pagina_atual=pagina,
    tamanho_pagina=tamanho,
    dados=dados_paginados,
  )


@app.post("/processar", response_model=RespostaProcessamento)
async def endpoint_processar_arquivos(
    requisicao: RequisicaoIntervaloDatas,
    pagina: int = Query(1, description="Número da página a ser retornada", ge=1),
    tamanho: int = Query(50, description="Quantidade de itens por página", ge=1),
) -> RespostaProcessamento:
  """
  Inicia o fluxo de processamento de dados e retorna os dados paginados no corpo da resposta.
  """
  if requisicao.data_inicio > requisicao.data_fim:
    raise HTTPException(
      status_code=status.HTTP_400_BAD_REQUEST,
      detail="A data de início não pode ser posterior à data de fim."
    )

  todos_os_registros = await executar_fluxo(requisicao.data_inicio, requisicao.data_fim)

  # Lógica para calcular a paginação dos resultados.
  total_de_registros = len(todos_os_registros)
  total_de_paginas = math.ceil(total_de_registros / tamanho) if total_de_registros > 0 else 0

  indice_inicio = (pagina - 1) * tamanho
  indice_fim = indice_inicio + tamanho
  dados_paginados = todos_os_registros[indice_inicio:indice_fim]

  if not todos_os_registros:
    mensagem = "O fluxo de trabalho terminou, mas nenhum dado foi processado."
  else:
    mensagem = f"Processados {total_de_registros} registros com sucesso."

  return RespostaProcessamento(
    mensagem=mensagem,
    total_registros=total_de_registros,
    total_paginas=total_de_paginas,
    pagina_atual=pagina,
    tamanho_pagina=tamanho,
    dados=dados_paginados,
  )
