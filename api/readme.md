# API de Processamento e Consulta de Dados do ONS

Este projeto consiste em uma API desenvolvida em Python com FastAPI, projetada para automatizar o processo de extração, transformação e consulta de dados públicos disponibilizados pelo Operador Nacional do Sistema Elétrico (ONS). A aplicação busca os arquivos de um pacote de dados específico, processa-os de forma concorrente e, opcionalmente, armazena-os em um ambiente cloud (Google Cloud Storage), além de fornecer um endpoint para consultar dados previamente armazenados em um data warehouse (Google BigQuery).

## Funcionalidades Principais

- **Extração de Dados da ONS:** Conecta-se à API de dados abertos da ONS para listar os recursos de dados disponíveis.
- **Processamento Concorrente:** Utiliza `asyncio` para baixar e processar múltiplos arquivos de dados em paralelo, otimizando o tempo de execução.
- **Seleção Inteligente de Formato:** Prioriza arquivos no formato Parquet sobre CSV quando ambos estão disponíveis para o mesmo período, visando maior eficiência.
- **Integração com Google Cloud:**
  - **Storage:** Realiza o upload dos arquivos processados para um bucket no Google Cloud Storage no formato Parquet.
  - **BigQuery:** Oferece um endpoint para consultar os dados já armazenados no BigQuery com filtros por intervalo de datas.
- **API Robusta:** Exposição de endpoints para iniciar o processamento e para realizar consultas, com paginação de resultados.

## Arquitetura e Tecnologias

O projeto é estruturado em módulos com responsabilidades bem definidas:

- `main.py`: Ponto de entrada da aplicação FastAPI. Define os endpoints, validações de entrada e orquestra as chamadas para os outros módulos.
- `processing.py`: Contém a lógica de orquestração do fluxo de processamento de dados, gerenciando a execução concorrente das tarefas.
- `service.py`: Isola toda a lógica de negócio e comunicação com serviços externos (API da ONS, Google Cloud Storage e BigQuery).
- `dto.py`: Define os modelos de dados (Data Transfer Objects) usando Pydantic para garantir a tipagem e validação das requisições e respostas da API.

**Stack Tecnológica:**
- **Linguagem:** Python 3.9+
- **Framework API:** FastAPI
- **Comunicação HTTP:** httpx (cliente assíncrono)
- **Manipulação de Dados:** pandas
- **Computação em Nuvem:** Google Cloud BigQuery, Google Cloud Storage
- **Execução Assíncrona:** asyncio

---

## Configuração do Ambiente

### Pré-requisitos
- Python 3.9 ou superior
- Uma conta no Google Cloud Platform com um projeto ativo.
- Credenciais do GCP configuradas no ambiente local (recomenda-se o uso do `gcloud auth application-default login`).
- Um bucket no Google Cloud Storage.
- Um dataset e uma tabela criados no Google BigQuery.

### Instalação

1.  **Clone o repositório:**
    ```sh
    git clone https://github.com/rillmind/sauterUniversityProject.git
    cd sauterUniversityProject
    ```

2.  **Crie e ative um ambiente virtual:**
    ```sh
    python -m venv venv
    source venv/bin/activate
    # No Windows: venv\Scripts\activate
    ```

3.  **Instale as dependências:**
    Crie um arquivo `requirements.txt` com o seguinte conteúdo e execute o comando `pip install`:
    ```
    # requirements.txt
    fastapi
    uvicorn[standard]
    pydantic
    python-dotenv
    httpx
    pandas
    pyarrow
    google-cloud-bigquery
    google-cloud-storage
    gcsfs
    ```
    ```sh
    pip install -r requirements.txt
    ```

4.  **Configure as variáveis de ambiente:**
    Crie um arquivo `.env` na raiz do projeto e preencha com as informações do seu ambiente Google Cloud.

    ```
    # .env
    BQ_DATASET_ID="seu_dataset_bigquery"
    BQ_TABLE_ID="sua_tabela_bigquery"
    GCS_BUCKET_NAME="nome-do-seu-bucket-gcs"
    GCP_PROJECT_ID="seu-id-de-projeto-gcp"
    ```

### Execução

Para iniciar a aplicação localmente, execute o seguinte comando na raiz do projeto:

```sh
uvicorn main:app --reload
```

A API estará disponível em http://127.0.0.1:8000, e a documentação interativa (Swagger UI) pode ser acessada em http://127.0.0.1:8000/docs.

## Endpoints da API

`POST /processar`

Inicia o fluxo de trabalho de busca e processamento dos arquivos da ONS para um determinado intervalo de datas. Os dados processados são retornados de forma paginada no corpo da resposta.

### Corpo da Requisição (JSON):

```json
{
  "data_inicio": "YYYY-MM-DD",
  "data_fim": "YYYY-MM-DD"
}
```

### Parâmetros de Query:

- `pagina` (int, opcional, default=1): Número da página.

- `tamanho` (int, opcional, default=50): Quantidade de registros por página.

### Exemplo de uso com curl:

``` sh
curl -X POST "[http://127.0.0.1:8000/processar?pagina=1&tamanho=10](http://127.0.0.1:8000/processar?pagina=1&tamanho=10)" \
-H "Content-Type: application/json" \
-d '{
  "data_inicio": "2022-01-01",
  "data_fim": "2022-12-31"
}'
```
