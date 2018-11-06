FROM python:3-alpine

MAINTAINER Jamotion <info@jamotion.ch>

RUN pip install --no-cache-dir jinja2

RUN  mkdir -p /opt/migrator/migrator
RUN  mkdir -p /opt/migrator/data
COPY migrator /opt/migrator/migrator
ADD migrate_repository.py /opt/migrator/
RUN chmod 0666 /opt/migrator/migrate_repository.py

WORKDIR /opt/migrator/data
VOLUME /opt/migrator/data

ENTRYPOINT ["python", "/opt/migrator/migrate_repository.py"]
CMD ["-h"]
