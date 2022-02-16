FROM python:3.8.12-alpine3.15

RUN mkdir -p /code/edr_connector && mkdir -p /logs

WORKDIR /code

ENV PYTHONPATH /code:$PYTHONPATH

COPY requirements.txt  /install/requirements.txt
RUN pip install -r /install/requirements.txt

COPY edr_connector /code/edr_connector/

ENTRYPOINT ["python3", "-u", "edr_connector/analyze.py"]
