all: volumes build up
DATA_FOLDER = ./srcs/data

build:
	@docker compose -f srcs/docker-compose.yml build

up:
	@docker compose -f srcs/docker-compose.yml up -d

down:
	@docker compose -f srcs/docker-compose.yml down --volumes

stop:
	@docker compose -f srcs/docker-compose.yml stop

clean:
	@docker system prune
	rm -rf srcs/data/www/avatars

fclean: down
	@docker system prune --all --force --volumes
	rm -rf srcs/data/www/avatars

volumes:
	@mkdir -p ./srcs/data/www

re: fclean all

.PHONY: all build up stop clean fclean re volumes
