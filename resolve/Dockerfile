# Resolve API — Python 3.12 (project requires 3.11+)
FROM python:3.12-slim

WORKDIR /app

# Install deps first for layer caching. sentence-transformers pulls torch —
# this image is intentionally the "full" one; for a lean dev image you can
# comment it out of requirements (the app lazy-loads it and tests use the
# built-in fake embedder).
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY mcp_server ./mcp_server
COPY evals ./evals
COPY data ./data

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
