
FROM python:3.6.8-alpine3.8

LABEL description="Panhandler"
LABEL version="2.0"
LABEL maintainer="sp-solutions@paloaltonetworks.com"

ENV TERRAFORM_VERSION=0.11.11
ENV TERRAFORM_SHA256SUM=94504f4a67bad612b5c8e3a4b7ce6ca2772b3c1559630dfd71e9c519e3d6149c
ENV CNC_USERNAME=paloalto
ENV CNC_PASSWORD=panhandler

WORKDIR /app
ADD requirements.txt /app/requirements.txt
ADD cnc/requirements.txt /app/cnc/requirements.txt
COPY src /app/src
COPY cnc /app/cnc

RUN apk add --update --no-cache git curl openssh gcc g++ make musl-dev python3-dev libffi-dev openssl-dev bash && \
    pip install --upgrade pip && pip install --no-cache-dir --no-use-pep517 -r requirements.txt && \
    pip install --no-cache-dir --no-use-pep517 -r cnc/requirements.txt && \
    apk del --no-cache gcc make g++ && \
    echo "===> Installing Terraform..."  && \
    curl https://releases.hashicorp.com/terraform/${TERRAFORM_VERSION}/terraform_${TERRAFORM_VERSION}_linux_amd64.zip > terraform_${TERRAFORM_VERSION}_linux_amd64.zip && \
    echo "${TERRAFORM_SHA256SUM}  terraform_${TERRAFORM_VERSION}_linux_amd64.zip" > terraform_${TERRAFORM_VERSION}_SHA256SUMS && \
    sha256sum -cs terraform_${TERRAFORM_VERSION}_SHA256SUMS && \
    unzip terraform_${TERRAFORM_VERSION}_linux_amd64.zip -d /bin && \
    rm -f terraform_${TERRAFORM_VERSION}_linux_amd64.zip  && \
    rm -f terraform_${TERRAFORM_VERSION}_SHA256SUMS && \
    if [ -f /app/cnc/db.sqlite3 ]; then rm /app/cnc/db.sqlite3; fi && \
    python /app/cnc/manage.py migrate && \
    python /app/cnc/manage.py shell -c "from django.contrib.auth.models import User; User.objects.create_superuser('${CNC_USERNAME}', 'admin@example.com', '${CNC_PASSWORD}')" && \
    chmod +x /app/cnc/start_app.sh

EXPOSE 80
ENTRYPOINT ["/app/cnc/start_app.sh"]
