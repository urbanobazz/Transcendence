#!/bin/bash
curl -kX POST https://localhost:8443/api/users/ \
-H "Content-Type: application/json" \
-H "Authorization: Bearer $TOKEN" \
-d "{\"username\":\"$1\"}"

