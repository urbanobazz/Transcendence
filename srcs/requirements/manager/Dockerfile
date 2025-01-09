FROM python:3.12-slim
# Set the Python path and working directory
ENV PYTHONPATH="/var/transcendence_scripts"
WORKDIR /var/transcendence_scripts

# Install additional packages for debugging
RUN apt-get update && apt-get install -y iputils-ping curl\
	build-essential \
	libpq-dev

# Copy and install dependencies
COPY conf/req.txt /var/req.txt
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir -r /var/req.txt

# Copy the entire manager project into the container
COPY tools /var/transcendence_scripts/
RUN chmod +x /var/transcendence_scripts/entrypoint.sh

# RUN python3 manage.py makemigrations && python3 manage.py migrate

# Set the DJANGO_SETTINGS_MODULE environment variable
ENV DJANGO_SETTINGS_MODULE=manager_service.settings
# Use the custom start script as the entry point
CMD ["/var/transcendence_scripts/entrypoint.sh"]
