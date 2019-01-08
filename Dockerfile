
FROM python:alpine

LABEL description="PanHandler"
LABEL version="0.1"
LABEL maintainer="sp-solutions@paloaltonetworks.com"

WORKDIR /app
ADD requirements.txt /app/requirements.txt
ADD cnc/requirements.txt /app/cnc-requirements.txt
RUN apk add --no-cache git
#RUN pip install -r requirements.txt
RUN pip install -r cnc-requirements.txt
COPY src /app/src
COPY cnc /app/cnc
#COPY tests /app/tests
RUN rm /app/cnc/db.sqlite3
RUN python /app/cnc/manage.py migrate
RUN python /app/cnc/manage.py shell -c "from django.contrib.auth.models import User; User.objects.create_superuser('pan', 'admin@example.com', 'panhandler')"

EXPOSE 80
CMD ["python", "/app/cnc/manage.py", "runserver", "0.0.0.0:80"]