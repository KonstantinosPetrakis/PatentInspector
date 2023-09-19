FROM ubuntu

COPY backend/requirements.txt /patentanalyzer/requirements.txt
COPY deploy/backend-entrypoint.sh /backend-entrypoint.sh

RUN apt update
# gdal-bin and libgdal-dev are required for GeoDjango, netcat is required for the entrypoint script
RUN apt install -y python3-pip gdal-bin libgdal-dev netcat
RUN pip install -r /patentanalyzer/requirements.txt
CMD sh ./backend-entrypoint.sh
