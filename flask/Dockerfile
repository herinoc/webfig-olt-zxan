FROM python:3.11-slim

# Set workdir
WORKDIR /app

# Install dependencies
COPY requirements.txt .
COPY run.py .
COPY app .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Expose flask port
EXPOSE 9693

# Run flask app
CMD ["python", "run.py"]

