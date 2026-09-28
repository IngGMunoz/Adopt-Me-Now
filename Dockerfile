# Imagen base ligera de Python
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Dependencias de Python (pymysql es puro Python: no requiere compiladores)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Código de la aplicación
COPY . .

# Ejecutar como usuario sin privilegios
RUN useradd --create-home appuser && mkdir -p static/uploads && chown -R appuser /app/static/uploads
USER appuser

EXPOSE 5100

CMD ["python", "app.py"]
