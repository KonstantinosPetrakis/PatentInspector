FROM ubuntu

COPY . /

RUN apt update
# gdal-bin and libgdal-dev are required for GeoDjango, netcat is required for the entrypoint script
RUN apt install -y python3-pip gdal-bin libgdal-dev netcat
RUN pip install -r requirements.txt
CMD bash ./deploy/django-entrypoint.sh
