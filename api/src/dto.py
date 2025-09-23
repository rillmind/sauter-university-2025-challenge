from datetime import date
from typing import List, Dict, Any

from pydantic import BaseModel


class IntervaloDeDatas(BaseModel):
  firstDate: date
  lastDate: date


class RespostaPaginada(BaseModel):
  total_items: int
  total_paginas: int
  pagina_atual: int
  items: List[Dict[str, Any]]
