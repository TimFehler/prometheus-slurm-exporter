FROM python:3.10

WORKDIR /usr/src/app

RUN pip install --no-cache-dir requests fabric prometheus_client 

COPY . .

CMD [ "python" , "./slurm_exporter.py"]


