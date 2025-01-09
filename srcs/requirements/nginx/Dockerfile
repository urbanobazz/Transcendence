FROM debian:11
RUN apt-get update && apt-get install --no-install-recommends -y nginx openssl && rm -rf /var/lib/apt/lists/*
RUN rm -fr /var/transcendence_scripts && mkdir -p /var/transcendence_scripts
COPY tools/create_cert.sh /var/transcendence_scripts
COPY conf/nginx.conf /etc/nginx/nginx.conf
RUN chmod -R +x /var/transcendence_scripts/ && chmod -R 755 /var/www/html && chown -R www-data:www-data /var/www/html
RUN /var/transcendence_scripts/create_cert.sh
CMD	["nginx", "-g", "daemon off;"]
