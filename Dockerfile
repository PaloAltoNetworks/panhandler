
FROM python:3.8-slim

LABEL description="Panhandler"
LABEL version="3.1"
LABEL maintainer="sp-solutions@paloaltonetworks.com"

ENV CNC_USERNAME=paloalto
ENV CNC_PASSWORD=panhandler
ENV CNC_HOME=/home/cnc_user
ENV CNC_APP=Panhandler
WORKDIR /app

RUN groupadd -g 999 cnc_group && \
    groupadd -g 998 docker && \
    useradd -r -m cnc_user -u 9001 -s /bin/bash -g cnc_group -G docker -G root && \
    mkdir /home/cnc_user/.pan_cnc && \
    chown cnc_user:cnc_group /home/cnc_user/.pan_cnc

ADD requirements.txt /app/requirements.txt

RUN apt-get update && \
    apt-get install -y --no-install-recommends git && \
    pip install --no-cache-dir -r requirements.txt && \
    apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false && \
    rm -rf /var/lib/apt/lists/*

COPY cnc /app/cnc
COPY src /app/src

RUN chown cnc_user /app/cnc

EXPOSE 8080
CMD ["/app/cnc/tools/ph.sh"]
