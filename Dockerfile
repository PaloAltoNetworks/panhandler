
FROM python:3.6.8-alpine3.8

LABEL description="Panhandler"
LABEL version="2.2"
LABEL maintainer="sp-solutions@paloaltonetworks.com"

ENV TERRAFORM_VERSION=0.11.13
ENV TERRAFORM_SHA256SUM=5925cd4d81e7d8f42a0054df2aafd66e2ab7408dbed2bd748f0022cfe592f8d2
ENV CNC_USERNAME=paloalto
ENV CNC_PASSWORD=panhandler

WORKDIR /app
ADD requirements.txt /app/requirements.txt

RUN apk add --update --no-cache git curl openssh gcc g++ make musl-dev python3-dev libffi-dev openssl-dev linux-headers bash && \
    pip install --upgrade pip && pip install --no-cache-dir --no-use-pep517 -r requirements.txt && \
    echo "===> Installing Terraform..."  && \
    curl https://releases.hashicorp.com/terraform/${TERRAFORM_VERSION}/terraform_${TERRAFORM_VERSION}_linux_amd64.zip > terraform_${TERRAFORM_VERSION}_linux_amd64.zip && \
    echo "${TERRAFORM_SHA256SUM}  terraform_${TERRAFORM_VERSION}_linux_amd64.zip" > terraform_${TERRAFORM_VERSION}_SHA256SUMS && \
    sha256sum -cs terraform_${TERRAFORM_VERSION}_SHA256SUMS && \
    unzip terraform_${TERRAFORM_VERSION}_linux_amd64.zip -d /bin && \
    rm -f terraform_${TERRAFORM_VERSION}_linux_amd64.zip  && \
    rm -f terraform_${TERRAFORM_VERSION}_SHA256SUMS

COPY cnc /app/cnc
COPY src /app/src

RUN if [ -f /app/cnc/db.sqlite3 ]; then rm /app/cnc/db.sqlite3; fi && \
    python /app/cnc/manage.py migrate && \
    python /app/cnc/manage.py shell -c "from django.contrib.auth.models import User; User.objects.create_superuser('${CNC_USERNAME}', 'admin@example.com', '${CNC_PASSWORD}')" && \
    chmod +x /app/cnc/start_app.sh

EXPOSE 80
ENTRYPOINT ["/app/cnc/start_app.sh"]
