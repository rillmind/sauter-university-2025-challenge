from fastapi import FastAPI, HTTPException, Query

from dto import IntervaloDeDatas, RespostaPaginada
from service import processar_por_ano_com_preview

app = FastAPI()


@app.post("/processar")
def processar(intervalo: IntervaloDeDatas, pagina: int = Query(1, ge=1)):
  try:
    page_size = 50
    max_items = pagina * page_size
    resultado = processar_por_ano_com_preview(
      first_date=intervalo.firstDate,
      last_date=intervalo.lastDate,
      preview_limit=max_items
    )
    total_items = int(resultado.get("total_registros", len(resultado["items"])))
    total_paginas = max(1, (total_items + page_size - 1) // page_size)
    pagina_atual = min(pagina, total_paginas)
    inicio = (pagina_atual - 1) * page_size
    fim = inicio + page_size
    itens_pagina = resultado["items"][inicio:fim] if inicio < len(resultado["items"]) else []
    preview = RespostaPaginada(
      total_items=total_items,
      total_paginas=total_paginas,
      pagina_atual=pagina_atual,
      items=itens_pagina
    )
    return {
      "mensagem": "Processamento concluído com sucesso.",
      "arquivos_parquet": resultado["arquivos_parquet"],  # URLs do GCS com parquet
      "preview": preview.model_dump()
    }
  except ValueError as ve:
    raise HTTPException(status_code=400, detail=str(ve))
  except Exception as e:
    raise HTTPException(status_code=500, detail=f"Falha ao processar: {e}")