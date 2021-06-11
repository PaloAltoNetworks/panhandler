
FROM registry.gitlab.com/panw-gse/as/as-py-base-image@sha256:b189d625a5386b7aff598d44e6822e02f0731e30061b890eaec68d658ac52e36

LABEL description="Panhandler"
LABEL version="4.5"
LABEL maintainer="tsautomatedsolutions@paloaltonetworks.com"

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

RUN groupadd -g 998 docker && \
    usermod cnc_user -G docker,root

RUN curl -k https://releases.hashicorp.com/terraform/${TERRAFORM_VERSION}/terraform_${TERRAFORM_VERSION}_linux_amd64.zip \
    > terraform_${TERRAFORM_VERSION}_linux_amd64.zip && \
    echo "${TERRAFORM_SHA256SUM}  terraform_${TERRAFORM_VERSION}_linux_amd64.zip" > terraform_${TERRAFORM_VERSION}_SHA256SUMS && \
    sha256sum -c --status --quiet terraform_${TERRAFORM_VERSION}_SHA256SUMS && \
    unzip terraform_${TERRAFORM_VERSION}_linux_amd64.zip -d /bin && \
    rm -f terraform_${TERRAFORM_VERSION}_linux_amd64.zip  && \
    rm -f terraform_${TERRAFORM_VERSION}_SHA256SUMS && \
    apt update && \
    apt install dos2unix

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade -r requirements.txt

COPY --chown=cnc_user:cnc_group tox.ini /app/
COPY --chown=cnc_user:cnc_group tests /app/tests/
COPY --chown=cnc_user:cnc_group cnc /app/cnc/
COPY --chown=cnc_user:cnc_group src /app/src/

RUN dos2unix cnc/tools/*

EXPOSE 8080
CMD ["/app/cnc/tools/ph.sh"]
