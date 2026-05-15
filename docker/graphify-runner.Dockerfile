FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends git curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir "graphifyy[ollama]"

WORKDIR /workspace

CMD ["python", "_tools/update_graph_snapshot.py", "--backend", "ollama"]
