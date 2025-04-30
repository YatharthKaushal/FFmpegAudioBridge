FROM python:3.10-slim

# Install system packages
RUN apt update && apt install -y ffmpeg

WORKDIR /app

# Copy your app
COPY . /app

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 5000

CMD ["python", "app.py"]

