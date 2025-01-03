import os 
import requests
from fabric import Connection
import time
from prometheus_client import start_http_server, Gauge

class RemoteClient:
    def __init__(self, hostname: str, user: str, port: int):
        """
        Initialize the RemoteClient with connection details.

        :param hostname: The hostname or IP address of the remote machine.
        :param user: The username for the remote machine.
        :param password: The password for the remote machine.
        :param port: The SSH port to connect to.
        """
        self.hostname = hostname
        self.user = user
        self.port = port
        self.key = "/usr/src/app/id_rsa"

    def run_command(self, command: str) -> str:
        """
        Run a command on the remote machine.

        :param command: The shell command to execute.
        :return: The command's output.
        """
        try:
            # Create a connection to the remote client using a public keyfile
            connection = Connection(
                host=self.hostname,
                user=self.user,
                connect_kwargs={"key_filename": self.key},
                port=self.port
            )

            # Run the command and capture the result
            result = connection.run(f"bash -lc '{command}'", hide=True)
            
            # Close the connection
            connection.close()

            return result.stdout.strip()
        except Exception as e:
            return f"An error occurred: {str(e)}"

if __name__ == "__main__":
    # Get the SSH connection details from environment variables
    SSH_HOST = os.environ.get('SLURM_SSH_HOST')
    SSH_USER = os.environ.get('SLURM_SSH_USER')
    SSH_PORT = os.environ.get('SLURM_SSH_PORT')

    SCRAPE_INTERVAL = int(os.environ.get('SCRAPE_INTERVAL'))

    # Create a RemoteClient instance
    client = RemoteClient(SSH_HOST, SSH_USER, SSH_PORT)

    # Start the Prometheus metrics server
    start_http_server(8000)

    # Create Prometheus gauges
    num_jobs_pending_gauge = Gauge("slurm_jobs_pending", "Number of jobs pending in the Slurm queue")
    num_jobs_running_gauge = Gauge("slurm_jobs_running", "Number of jobs running in the Slurm queue")

    num_nodes_total_gauge = Gauge("slurm_nodes_total", "Total number of nodes in the Slurm cluster")
    num_nodes_allocated_gauge = Gauge("slurm_nodes_allocated", "Number of nodes allocated in the Slurm cluster")
    num_nodes_mixed_gauge = Gauge("slurm_nodes_mixed", "Number of nodes in mixed state in the Slurm cluster")
    num_nodes_idle_gauge = Gauge("slurm_nodes_idle", "Number of nodes idle in the Slurm cluster")
    num_nodes_down_gauge = Gauge("slurm_nodes_down", "Number of nodes down in the Slurm cluster")

    # Continuously update the Prometheus gauges
    while True:
        num_jobs_pending = client.run_command("squeue -h --array -t pending | wc -l")
        num_jobs_pending_gauge.set(int(num_jobs_pending))

        num_jobs_running = client.run_command("squeue -h --array -t running | wc -l")
        num_jobs_running_gauge.set(int(num_jobs_running))

        num_nodes_total = client.run_command("sinfo -N -h | awk {print\ \$1} | sort | uniq | wc -l")
        num_nodes_total_gauge.set(int(num_nodes_total))

        num_nodes_allocated = client.run_command("sinfo -N -h --state=alloc | awk {print\ \$1} | sort | uniq | wc -l")
        num_nodes_allocated_gauge.set(int(num_nodes_allocated))

        num_nodes_mixed = client.run_command("sinfo -N -h --state=mixed | awk {print\ \$1} | sort | uniq | wc -l")
        num_nodes_mixed_gauge.set(int(num_nodes_mixed))

        num_nodes_idle = client.run_command("sinfo -N -h --state=idle | awk {print\ \$1} | sort | uniq | wc -l")
        num_nodes_idle_gauge.set(int(num_nodes_idle))

        num_nodes_down = client.run_command("sinfo -N -h --state=down | awk {print\ \$1} | sort | uniq | wc -l")
        num_nodes_down_gauge.set(int(num_nodes_down))

        time.sleep(SCRAPE_INTERVAL)