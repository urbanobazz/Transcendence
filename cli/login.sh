#!/bin/bash
curl -kX POST https://localhost:8443/api/login/ \
-H "Content-Type: application/json" \
-d "{\"username\":\"$1\", \"password\":\"$2\"}"
