FROM python:3.9-slim

WORKDIR /app

# ডিপেন্ডেন্সি ইনস্টল
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# কোড কপি
COPY . .

# ডিরেক্টরি তৈরি
RUN mkdir -p data sessions

# বট চালান
CMD ["python", "bot.py"]
