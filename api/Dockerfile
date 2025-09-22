FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir \
  fastapi==0.104.1 \
  uvicorn[standard]==0.24.0 \
  pydantic==2.5.0 \
  pytest==7.4.3 \
  pytest-asyncio==0.21.1 \
  httpx==0.25.2 \
  pandas==2.3.2 \
  numpy==2.3.3 \
  requests==2.32.4 \
  requests-file==2.0.0 \
  requests-ftp==0.3.1 \

COPY . .

# Expor a porta que a aplicação vai usar
EXPOSE 8000

# Comando para iniciar a aplicação
CMD ["uvicorn", "api.app.main:app", "--host", "0.0.0.0", "--port", "8000"]