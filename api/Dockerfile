FROM python:3.11-slim as builder

WORKDIR /install

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

COPY requirements.txt .
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir -r requirements.txt

###

FROM python:3.11-slim

RUN useradd --create-home --shell /bin/bash appuser
WORKDIR /home/appuser/app
USER appuser

COPY --from=builder /opt/venv /opt/venv

COPY ./app .

ENV PATH="/opt/venv/bin:$PATH"

EXPOSE 8080

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
