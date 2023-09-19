FROM node:16-alpine

COPY frontend /frontend
COPY deploy/* /frontend
WORKDIR /frontend
RUN apk add jq
RUN npm i
CMD sh frontend-entrypoint.sh