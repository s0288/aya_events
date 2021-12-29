FROM python:3-alpine

WORKDIR '/app'

# install dependencies
COPY requirements.txt .
RUN \
 apk add --no-cache postgresql-libs && \
 apk add --no-cache --virtual .build-deps gcc musl-dev postgresql-dev && \
 pip install -r requirements.txt --no-cache-dir && \
 apk --purge del .build-deps
# install module
COPY setup.py .
RUN python setup.py develop

# mount relevant directories
COPY ./src .

CMD python run_telegram.py