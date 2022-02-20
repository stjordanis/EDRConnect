FROM python:3.8.12-alpine3.15

RUN mkdir -p /code/edr_connect && mkdir -p /logs

WORKDIR /code

ENV PYTHONPATH /code:$PYTHONPATH

COPY requirements.txt  /install/requirements.txt
RUN pip install -r /install/requirements.txt

COPY edr_connect /code/edr_connect/

ENTRYPOINT ["python3", "-u", "edr_connect/analyze.py"]
