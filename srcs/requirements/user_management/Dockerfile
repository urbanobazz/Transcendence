# Use the official Python 3.12 slim image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONPATH="/var/transcendence_scripts"

# Set the working directory inside the container
WORKDIR /var/transcendence_scripts

RUN mkdir -p /var/transcendence_scripts/data

RUN apt-get update && apt-get install -y \
	build-essential \
	libpq-dev libjpeg-dev zlib1g-dev libpng-dev \
	libtiff-dev libfreetype6-dev curl\
	&& rm -rf /var/lib/apt/lists/*

# Copy the requirements file and install dependencies
COPY conf/req.txt /var/req.txt
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir -r /var/req.txt

# Copy the application code
COPY tools/ /var/transcendence_scripts/

# Default command to run when the container starts

# Start by running makemigrations, migrate, and then start the Daphne server
CMD ["sh", "-c", "python3 manage.py makemigrations && python3 manage.py migrate && daphne -b 0.0.0.0 -p 8000 management_service.asgi:application"]
#CMD ["sh", "-c", "python3 manage.py makemigrations && python3 manage.py migrate && gunicorn management_service.Wsgi:application --bind 0.0.0.0:8000"]
