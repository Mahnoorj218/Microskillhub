FROM python:3.12-slim

WORKDIR /app

# Install Python dependencies
COPY Backend/requirements.txt /app/Backend/requirements.txt
RUN pip install --no-cache-dir -r /app/Backend/requirements.txt

# Copy application (API + frontend)
COPY Backend/ /app/Backend/
COPY Frontend/ /app/Frontend/

WORKDIR /app/Backend

ENV PYTHONUNBUFFERED=1

# Railway sets PORT at runtime
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
