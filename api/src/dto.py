from datetime import date
from typing import List, Dict, Any

from pydantic import BaseModel


class RequisicaoIntervaloDatas(BaseModel):
  data_inicio: date
  data_fim: date


class RespostaProcessamento(BaseModel):
  mensagem: str
  total_registros: int
  total_paginas: int
  pagina_atual: int
  tamanho_pagina: int
  dados: List[Dict[str, Any]]
