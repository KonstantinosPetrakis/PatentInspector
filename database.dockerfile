FROM postgis/postgis

RUN apt update
RUN apt install -y python3-pip
RUN pip install gdown
