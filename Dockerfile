FROM python:3.9-slim

WORKDIR /app
COPY . .

# Cài đặt các package cho cả backend và frontend
RUN pip install -r requirements.txt

# Chạy cả hai app song song
CMD ["sh", "-c", "python app.py >> backend.txt && python load_script.py >> frontend.txt"]
