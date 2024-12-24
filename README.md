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
Use the `-d` to detach from the running container.

## Author 

Tim Fehler - Dec 2024
