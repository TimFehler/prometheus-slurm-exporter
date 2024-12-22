# Remote SLURM Prometheus Exporter

Expose metrics of a SLURM instance only accessible via SSH to Prometheus.

## Development

Build Docker image with
```
docker build -t slurm_exporter .
```

Run Docker image with
```
docker run slurm_exporter
```

## Author 

Tim Fehler - Dec 2024
