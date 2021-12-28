FROM python:3.7-slim

WORKDIR '/app'

# install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt
# install module
COPY setup.py .
RUN python setup.py develop

# mount relevant directories
COPY ./src .

CMD python run_telegram.py