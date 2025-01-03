# Remote SLURM Prometheus Exporter

Expose metrics of a SLURM instance only accessible via SSH to Prometheus.

## Development

Build Docker image with
```
docker compose build
```

Run Docker image with
```
docker compose up [-d]
```
Use the flag `-d` to detach from the running container.

The metric should then be accessible on localhost using the port specified via environmental variables. You can test the exporter is working properly with

```bash
curl localhost:<port>
```

## Environment

Environmental variables are specified in the file `.env` and then used in both the Docker Compose file and the actual Python script. The repository contains an example `.env_example`, adjust this file to your needs.

## Author 

Tim Fehler - Dec 2024
