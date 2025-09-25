import asyncio
from datetime import date
from typing import List, Dict, Any

import service


async def executar_fluxo(data_inicio: date, data_fim: date) -> List[Dict[str, Any]]:
  """
  Orquestra todo o fluxo de trabalho para o intervalo de datas, retornando todos os dados.
  """
  print("Buscando a lista de recursos da ONS...")
  todos_os_recursos = await service.obter_recursos_ons()
  if not todos_os_recursos:
    print("Não foi possível obter os recursos da ONS.")
    return []

  print("Filtrando pelo melhor formato disponível...")
  recursos_para_processar = service.filtrar_recursos_por_ano_e_formato(
    todos_os_recursos, data_inicio, data_fim
  )

  if not recursos_para_processar:
    print(f"Nenhum recurso encontrado para o período solicitado.")
    return []

  print(f"Encontrados {len(recursos_para_processar)} recursos. Iniciando processamento paralelo...")

  # Cria uma lista de tarefas para serem executadas de forma concorrente.
  tarefas = [service.processar_recurso(res) for res in recursos_para_processar]
  resultados = await asyncio.gather(*tarefas)

  # "Achata" a lista de listas de resultados em uma única lista de registros.
  todos_os_registros = [registro for lista_resultado in resultados for registro in lista_resultado if lista_resultado]

  print(f"Fluxo de trabalho concluído. Total de {len(todos_os_registros)} registros processados.")
  return todos_os_registros
