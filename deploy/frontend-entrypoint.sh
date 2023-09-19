#!/bin/bash

API_URL="$DOMAIN/api"

rm ./src/config.json
jq -n \
    --arg API_URL "$API_URL" \
    --arg DEBUG false \
    '
    {
        API_URL: $API_URL,
        DEBUG: $DEBUG | test("true")
    }
    ' > ./src/config.json
cat ./src/config.json
npm run build