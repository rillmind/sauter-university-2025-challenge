# API de Processamento de Dados ONS

Este projeto consiste em uma API desenvolvida em Python com FastAPI, projetada para automatizar o processo de extração, transformação e consulta de dados públicos disponibilizados pelo Operador Nacional do Sistema Elétrico (ONS). A aplicação busca os arquivos de um pacote de dados específico, processa-os de forma concorrente e, opcionalmente, armazena-os em um ambiente cloud (Google Cloud Storage), além de fornecer um endpoint para consultar dados previamente armazenados em um data warehouse (Google BigQuery).

## Funcionalidades

- **Consulta BigQuery**: Busca dados históricos armazenados no BigQuery por intervalo de datas
- **Processamento ONS**: Baixa, processa e converte dados do portal da ONS para formato Parquet
- **Paginação**: Suporte a paginação para grandes volumes de dados
- **Armazenamento GCS**: Upload automático de arquivos processados para Google Cloud Storage
- **Processamento Paralelo**: Execução concorrente para otimizar desempenho

## Tecnologias

- **FastAPI**: Framework web moderno e de alta performance
- **Pydantic**: Validação de dados e serialização
- **Pandas**: Manipulação e análise de dados
- **Google Cloud BigQuery**: Data warehouse para consultas SQL
- **Google Cloud Storage**: Armazenamento de arquivos
- **HTTPX**: Cliente HTTP assíncrono
- **Docker**: Containerização da aplicação

## Configuração

### Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto com as seguintes variáveis:

```env
# Google Cloud Platform
GCP_PROJECT_ID=seu-projeto-gcp
BQ_DATASET_ID=seu-dataset
BQ_TABLE_ID=sua-tabela
GCS_BUCKET_NAME=seu-bucket-gcs

# Configurações opcionais podem ser adicionadas aqui
```

### Instalação Local

1. Clone o repositório:
```bash
git clone https://github.com/rillmind/sauter-university-2025-challenge.git
cd sauter-university-2025-challenge/api
```

2. Instale as dependências:
```bash
pip install -r requirements.txt
```

3. Configure as credenciais do Google Cloud:
```bash
gcloud auth application-default login
# ou configure a variável GOOGLE_APPLICATION_CREDENTIALS
```

4. Execute a aplicação:
```bash
uvicorn main:app --host 0.0.0.0 --port 8080 --reload
```

### Instalação com Docker

1. Build da imagem:
```bash
docker build -t api-ons .
```

2. Execute o container:
```bash
docker run -p 8080:8080 --env-file .env api-ons
```

## Endpoints

### Consultar Dados no BigQuery
```
GET /consultar
```

Consulta dados históricos no BigQuery por intervalo de datas com paginação.

**Parâmetros:**
- `data_inicio` (date): Data de início no formato AAAA-MM-DD
- `data_fim` (date): Data de fim no formato AAAA-MM-DD  
- `pagina` (int, opcional): Número da página (padrão: 1)
- `tamanho` (int, opcional): Itens por página (padrão: 20)

**Exemplo:**
```bash
curl "http://localhost:8080/consultar?data_inicio=2023-01-01&data_fim=2023-12-31&pagina=1&tamanho=50"
```

### Processar Dados da ONS
```
POST /processar
```

Baixa e processa dados do portal da ONS para o período especificado.

**Corpo da Requisição:**
```json
{
  "data_inicio": "2023-01-01",
  "data_fim": "2023-12-31"
}
```

**Parâmetros de Query:**
- `pagina` (int, opcional): Número da página (padrão: 1)
- `tamanho` (int, opcional): Itens por página (padrão: 50)

**Exemplo:**
```bash
curl -X POST "http://localhost:8080/processar?pagina=1&tamanho=100" \
  -H "Content-Type: application/json" \
  -d '{"data_inicio": "2023-01-01", "data_fim": "2023-12-31"}'
```

### Resposta Padrão

Ambos os endpoints retornam a seguinte estrutura:

```json
{
  "mensagem": "Descrição do resultado",
  "total_registros": 1500,
  "total_paginas": 30,
  "pagina_atual": 1,
  "tamanho_pagina": 50,
  "dados": [
    {
      "campo1": "valor1",
      "campo2": "valor2"
    }
  ]
}
```

## Arquitetura

### Fluxo de Processamento

1. **Busca de Recursos**: Consulta a API da ONS para obter lista de recursos disponíveis
2. **Filtro por Formato**: Seleciona o melhor formato disponível (Parquet > CSV) para cada ano
3. **Processamento Paralelo**: Baixa e processa múltiplos recursos simultaneamente
4. **Conversão**: Converte dados para formato Parquet uniformizado
5. **Upload GCS**: Armazena arquivos processados no Google Cloud Storage
6. **Retorno**: Retorna dados processados com paginação

## Desenvolvimento

### Executar em Modo de Desenvolvimento

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8080
```

### Documentação da API

Após iniciar a aplicação, acesse:
- Swagger UI: `http://localhost:8080/docs`
- ReDoc: `http://localhost:8080/redoc`

## Monitoramento

A aplicação inclui logs detalhados para monitoramento do processamento:

- Status de download de recursos
- Progresso de conversão de arquivos
- Estatísticas de processamento
- Erros e exceções

## Considerações

- **Rate Limiting**: A API da ONS pode ter limitações de taxa
- **Memória**: Processamento de grandes volumes pode exigir recursos significativos
- **Timeout**: Downloads podem demorar dependendo do tamanho dos arquivos
- **Credenciais**: Certifique-se de que as credenciais do GCP estão configuradas corretamente
