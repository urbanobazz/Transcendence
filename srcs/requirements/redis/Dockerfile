FROM	debian:latest
RUN		apt-get update && \
		apt-get install -y redis && \
		rm -rf /var/lib/apt/lists/*
RUN		mkdir /var/transcendence_scripts
COPY	./tools/redis.sh /var/transcendence_scripts/
COPY	./conf/redis.conf /etc/redis/
RUN		chmod +x /var/transcendence_scripts/redis.sh
CMD		["/var/transcendence_scripts/redis.sh"]
