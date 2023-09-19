#!/bin/bash

if [ ! -f "./server.crt" ]; then
    echo "No certificates found, generating dummy ones..."
    apt update &> /dev/null 
    apt install -y openssl &> /dev/null
    openssl req -x509 -newkey rsa:4096 -keyout server.key -out server.crt -sha256 -days 3650 -nodes -subj "/C=XX/ST=StateName/L=CityName/O=CompanyName/OU=CompanySectionName/CN=CommonNameOrHostname" &> /dev/null
else
    echo "Certificates found, skipping dummy generation..."
fi