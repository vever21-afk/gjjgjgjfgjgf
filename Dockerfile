FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt ./
RUN pip install --upgrade pip setuptools wheel && pip install --no-cache-dir -r requirements.txt

COPY . .

# Render injects PORT env; default to 10000 if not present
CMD ["python", "app.py"]
