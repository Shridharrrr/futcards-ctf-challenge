FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Flag lives at /flag.txt (outside /app so it's not trivially browsable)
RUN cp flag.txt /flag.txt && rm flag.txt

EXPOSE 5000

CMD ["python", "app.py"]
