FROM python:3.12-slim
#EXPOSE 
# ENV PYTHONPATH="/var/transcendence_scripts"
WORKDIR /var
COPY conf/req.txt /var/req.txt
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir -r /var/req.txt
COPY tools/ /var/project/
WORKDIR /var/project
# COPY tools/entrypoint.sh /var/entrypoint.sh
# RUN chmod +x entrypoint.sh
# CMD ["/var/entrypoint.sh"]
CMD ["daphne", "-b", "0.0.0.0", "-p", "8001", "ai_service.asgi:application"]
