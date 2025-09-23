# --- Estágio 1: Build ---
# Usamos uma imagem Python completa para instalar as dependências.
# Isso nos dá acesso a ferramentas de compilação que podem ser necessárias.
FROM python:3.11-slim as builder

# Define o diretório de trabalho dentro do container
WORKDIR /app

# Copia o arquivo de dependências para o container
COPY requirements.txt .

# Instala as dependências em um diretório local, o que facilita copiá-las depois
RUN pip install --no-cache-dir --user -r requirements.txt

# --- Estágio 2: Final ---
# Usamos a mesma imagem base, mas "limpa", sem as ferramentas de build.
FROM python:3.11-slim

# Define o diretório de trabalho
WORKDIR /app

# Cria um usuário não-root para rodar a aplicação (boa prática de segurança)
RUN useradd --create-home appuser
USER appuser

# Copia as dependências que foram instaladas no estágio de "builder"
COPY --from=builder /home/appuser/.local /home/appuser/.local

# Copia todos os arquivos da sua API (.py) para o diretório de trabalho
COPY . .

# Expõe a porta que o Gunicorn vai usar
EXPOSE 8080

# Define a variável de ambiente PATH para que o executável do gunicorn seja encontrado
ENV PATH="/home/appuser/.local/bin:${PATH}"

# O comando para iniciar a aplicação quando o container rodar.
# Usamos Gunicorn como um servidor de produção para o Uvicorn.
# A variável $PORT é fornecida automaticamente pelo Cloud Run.
CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8080", "main:app"]
