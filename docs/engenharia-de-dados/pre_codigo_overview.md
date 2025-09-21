# Projeto ENA Diário por Reservatório – Fase Pré-Código

## 1. Objetivo da Fase
Consolidar os dados diários de ENA por reservatório, integrando múltiplos datasets anuais (2000–2025) em uma base única padronizada, limpa e estruturada. Esta base será utilizada para análise exploratória, dashboards e modelagem preditiva.  

A fase pré-código inclui:  
- Revisão de requisitos do projeto e schema dos dados  
- Definição de convenções de nomenclatura, armazenamento e políticas  
- Coordenação com DevOps para provisionamento de Service Account  
- Planejamento da consolidação de dados no pipeline Bronze → Silver → Gold  

---

## 2. Revisão de Requisitos do Projeto

- **Fonte de dados:** ONS – Energia Natural Afluente (ENA) diária por reservatório  
- **Período:** 2000 a 2025 (datasets separados por ano)  
- **Formato Original:** Parquet  
- **Frequência de atualização:** Diária  
- **Objetivo:** Consolidar os datasets anuais em uma base unificada, mantendo consistência e integridade das colunas essenciais.

### 2.1 Colunas Essenciais (Atualizado conforme Dicionário de Dados)
| Coluna | Tipo | Descrição | Regras de Validação |
|--------|------|-----------|---------------------|
| ear_data | DATE | Data da observação (séries temporais) | Não nulo, formato YYYY-MM-DD |
| cod_resplanejamento | **INT64** | Código único do reservatório | Não nulo, não zero, não negativo |
| nom_reservatorio | STRING | Nome do reservatório | Não nulo, 20 posições |
| ear_total_mwmes | FLOAT | Energia armazenada total (MWmes) – **variável alvo principal** | Não nulo, permite zero, não negativo |
| ear_maxima_total_mwmes | FLOAT | Capacidade máxima do reservatório | Não nulo, permite zero, não negativo |
| ear_reservatorio_percentual | FLOAT | Percentual de energia armazenada (**variável alvo alternativa**) | Não nulo, permite zero, não negativo |
| val_contribearbacia | FLOAT | Contribuição do reservatório para a bacia (%) | Não nulo, permite zero, não negativo |
| val_contribearsin | FLOAT | Contribuição para o SIN (%) | Não nulo, permite zero, não negativo |
| nom_bacia | STRING | Nome da bacia hidrográfica | Não nulo, 15 posições |
| nom_subsistema | STRING | Subsistema (S, SE, N etc.) | Não nulo, 20 posições |
| nom_ree | STRING | Reservatório de Energia Equivalente (REE) | Permite nulo, 20 posições |
| tip_reservatorio | STRING | Tipo do reservatório (com/sem usina) | Não nulo, 40 posições |

**Colunas adicionais úteis (conforme dicionário):**  
- `ear_reservatorio_subsistema_proprio_mwmes` (FLOAT, não nulo, permite zero, não negativo)
- `ear_reservatorio_subsistema_jusante_mwmes` (FLOAT, não nulo, permite zero, não negativo)  
- `earmax_reservatorio_subsistema_proprio_mwmes` (FLOAT, não nulo, permite zero, não negativo)
- `earmax_reservatorio_subsistema_jusante_mwmes` (FLOAT, não nulo, permite zero, não negativo)
- `val_contribearmaxbacia` (FLOAT, não nulo, permite zero, não negativo)
- `val_contribearsubsistema` (FLOAT, não nulo, permite zero, não negativo)
- `val_contribearmaxsubsistema` (FLOAT, não nulo, permite zero, não negativo)
- `val_contribearsubsistemajusante` (FLOAT, não nulo, permite zero, não negativo)
- `val_contribearmaxsubsistemajusante` (FLOAT, não nulo, permite zero, não negativo)
- `val_contribearmaxsin` (FLOAT, não nulo, permite zero, não negativo)

**Variáveis Alvo (Target):**  
- Primária: `ear_total_mwmes`  
- Alternativa: `ear_reservatorio_percentual`

**Metadados de ingestão:**
- `_file_source` (STRING): Nome do arquivo origem
- `_ingestion_timestamp` (TIMESTAMP): Data/hora da ingestão

---

## 3. Convenções e Políticas (Atualizado)

### 3.1 Naming
- **Bucket GCS único:**  
  - `gs://ena-data-project-sauter-hydro-forecast/bronze/` → arquivos originais (2000–2025 em parquet)  
  - `gs://ena-data-project-sauter-hydro-forecast/silver/` → dados limpos e normalizados  
  - `gs://ena-data-project-sauter-hydro-forecast/gold/` → dados agregados para análise/modelagem  

- **Dataset BigQuery:**  
  - `ena_analytics`  

- **Tabelas BigQuery:**  
  - `ena_consolidado` (particionada por `ear_data` e clusterizada em `cod_resplanejamento`, `nom_subsistema`)  

- **Service Accounts:**  
  - `github-actions-sa@project-sauter-hydro-forecast.iam.gserviceaccount.com` (CI/CD)  
  - `sa-ena-pipeline@project-sauter-hydro-forecast.iam.gserviceaccount.com` (ingestão ENA)  

---

### 3.2 Storage
- **Formato:** Parquet (Snappy)  
- **Particionamento (BigQuery):** `DATE(ear_data)`  
- **Clustering (BigQuery):** `cod_resplanejamento, nom_subsistema`  
- **Políticas de ciclo de vida (a definir):**  
  - Bronze: 90 dias  
  - Silver: 365 dias  
  - Gold: indefinido  

---

### 3.3 Qualidade de Dados
- **Validações obrigatórias:** conforme dicionário de dados (nulos, zeros, negativos)  
- **Completude:** registrar taxa de preenchimento por coluna  
- **Consistência:** validar ranges temporais e chaves únicas  
- **Integridade referencial:** validar consistência entre anos  

---

### 3.4 IAM
- **GitHub Actions SA:**  
  - Permissões:  
    - `roles/run.admin`  
    - `roles/storage.admin`  
    - `roles/bigquery.admin`  
    - `roles/iam.serviceAccountUser`  

- **ENA Pipeline SA:**  
  - Permissões:  
    - `roles/storage.objectCreator`  
    - `roles/bigquery.dataEditor`  
    - `roles/secretmanager.secretAccessor`  

---

## 4. Coordenação com DevOps (IAM & Permissões)

### 4.1 Service Account
- **Nome:** `sa-ingest-ena@project-id.iam.gserviceaccount.com`  
- **Função:** Ingestão e consolidação de dados  

### 4.2 Permissões mínimas
- `roles/storage.objectCreator` (bucket bronze)  
- `roles/storage.objectCreator` (buckets silver/gold)  
- `roles/bigquery.dataEditor` no dataset alvo  
- `roles/secretmanager.secretAccessor` (acesso a chaves)  
- `roles/composer.worker` (se Cloud Composer/Airflow for usado)  

### 4.3 Gestão de Chaves
- Chave SA armazenada no Secret Manager  
- Rotação automática de chaves a cada 90 dias  
- Time valida acesso: `gcloud auth activate-service-account --key-file=...`  

**Deliverable:** Checklist de SA criada  

---

## 5. Checklist de Aceite da Fase Pré-Código

| Item | Status | Responsável |
|------|--------|-------------|
| Schema definido conforme dicionário oficial (`schema_frequency.md`) | ✅ | Eng. Dados |
| Convenções e políticas documentadas (`CONVENTIONS.md`) | ✅ | Eng. Dados |
| Regras de validação implementadas conforme dicionário | ⏳ | Eng. Dados |
| Service Account provisionada e testada | ✅ | DevOps |
| Acessos validados pela equipe | ✅ | Time |
| Pipeline de consolidação 2000-2025 planejado | ✅ | Eng. Dados |
| Protocolos de qualidade baseados no dicionário | ⏳ | Eng. Dados |

---

## 6. Próximos Passos

1. **Implementar validações específicas** baseadas no dicionário de dados
2. **Criar processo de tratamento** para dados que violam regras de qualidade
3. **Documentar exceções** encontradas nos dados históricos (2000-2025)
4. **Preparar ambiente** para a carga completa do período

**Documentação adicional:**
- `DATA_DICTIONARY.md` - Baseado no documento oficial fornecido
- `QUALITY_CHECKS.md` - Protocolos de validação específicos
- `VALIDATION_RULES.md` - Regras detalhadas de qualidade

---
