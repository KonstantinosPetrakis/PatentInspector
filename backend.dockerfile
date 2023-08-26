FROM ubuntu

COPY requirements.txt /patentanalyzer/requirements.txt

RUN apt update
# gdal-bin and libgdal-dev are required for GeoDjango, netcat is required for the entrypoint script
RUN apt install -y python3-pip gdal-bin libgdal-dev netcat
RUN pip install -r /patentanalyzer/requirements.txt
CMD bash /patentanalyzer/deploy/django-entrypoint.sh
