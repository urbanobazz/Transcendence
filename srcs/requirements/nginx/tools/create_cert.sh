#!/bin/bash
openssl req -x509 -newkey rsa:4096 -keyout /var/key.pem -out /var/cert.pem -days 365 -nodes -subj "/C=DE/ST=Berlin/L=Berlin/O=PONG TRANSCENDENCE PONG at 42 Berlin/CN=www.nyan.cat"
