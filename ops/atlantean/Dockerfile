# Atlantean Sovereignty production service container
FROM python:3.11-slim

WORKDIR /app

# Create runtime user and writable data directory for SQLite.
RUN useradd --system --uid 1000 atlantean \
    && mkdir -p /data \
    && chown atlantean:atlantean /data

COPY server/atlantean_server.py server/atlantean_server.py

USER atlantean
ENV PYTHONUNBUFFERED=1 \
    ATLANTEAN_HOST=0.0.0.0 \
    ATLANTEAN_DB=/data/atlantean_prod.sqlite

VOLUME ["/data"]
EXPOSE 8080

ENTRYPOINT ["python3", "server/atlantean_server.py"]
