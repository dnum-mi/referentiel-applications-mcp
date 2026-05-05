FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY server.py ./

ENV REFAPP_DIR=/work/refapp

CMD ["python", "server.py"]
