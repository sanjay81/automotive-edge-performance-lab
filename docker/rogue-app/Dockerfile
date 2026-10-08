FROM python:3.12-slim

WORKDIR /app

RUN pip install requests PyYAML

COPY load.py .

CMD ["python", "-u", "load.py"]
