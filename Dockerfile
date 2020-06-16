
FROM python:3.8-slim

LABEL description="Panhandler"
LABEL version="3.3"
LABEL maintainer="sp-solutions@paloaltonetworks.com"

ENV TERRAFORM_VERSION=0.11.13
ENV TERRAFORM_SHA256SUM=5925cd4d81e7d8f42a0054df2aafd66e2ab7408dbed2bd748f0022cfe592f8d2
ENV CNC_USERNAME=paloalto
ENV CNC_PASSWORD=panhandler
ENV CNC_HOME=/home/cnc_user
ENV CNC_APP=Panhandler
# fix for #209
ENV COLUMNS=80
ENV PYTHONHTTPSVERIFY=0
WORKDIR /app

RUN groupadd -g 999 cnc_group && \
    groupadd -g 998 docker && \
    useradd -r -m cnc_user -u 9001 -s /bin/bash -g cnc_group -G docker -G root && \
    mkdir /home/cnc_user/.pan_cnc && \
    chown cnc_user:cnc_group /home/cnc_user/.pan_cnc

RUN apt-get update && \
    apt-get install -y --no-install-recommends git build-essential libffi-dev curl unzip openssh-client && \
    apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false && \
    rm -rf /var/lib/apt/lists/*

RUN curl -k https://releases.hashicorp.com/terraform/${TERRAFORM_VERSION}/terraform_${TERRAFORM_VERSION}_linux_amd64.zip \
    > terraform_${TERRAFORM_VERSION}_linux_amd64.zip && \
    echo "${TERRAFORM_SHA256SUM}  terraform_${TERRAFORM_VERSION}_linux_amd64.zip" > terraform_${TERRAFORM_VERSION}_SHA256SUMS && \
    sha256sum -c --status --quiet terraform_${TERRAFORM_VERSION}_SHA256SUMS && \
    unzip terraform_${TERRAFORM_VERSION}_linux_amd64.zip -d /bin && \
    rm -f terraform_${TERRAFORM_VERSION}_linux_amd64.zip  && \
    rm -f terraform_${TERRAFORM_VERSION}_SHA256SUMS

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=cnc_user:cnc_group cnc src tests tox.ini /app/

EXPOSE 8080
CMD ["/app/cnc/tools/ph.sh"]
