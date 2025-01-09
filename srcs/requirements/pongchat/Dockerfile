FROM python:3.12-slim
ENV PYTHONPATH="/var/transcendence_scripts"
WORKDIR /var/transcendence_scripts
COPY conf/req.txt /var/req.txt
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir -r /var/req.txt
COPY tools/ /var/transcendence_scripts/
CMD ["daphne", "-b", "0.0.0.0", "-p", "8003", "chat_manager.asgi:application"]
