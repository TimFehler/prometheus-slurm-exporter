import os 
import sys
import requests
from fabric import Connection
import time
from prometheus_client import start_http_server, Gauge

SSH_HOST = os.environ.get('SLURM_SSH_HOST')
SSH_USER = os.environ.get('SLURM_SSH_USER')
SSH_PASS = os.environ.get('SLURM_SSH_PASS')
SSH_PORT = os.environ.get('SLURM_SSH_PORT')   


class RemoteClient:
    def __init__(self, hostname: str, user: str, password: str, port: int):
        """
        Initialize the RemoteClient with connection details.

        :param hostname: The hostname or IP address of the remote machine.
        :param user: The username for the remote machine.
        :param password: The password for the remote machine.
        :param port: The SSH port to connect to.
        """
        self.hostname = hostname
        self.user = user
        self.password = password
        self.port = port

    def run_command(self, command: str) -> str:
        """
        Run a command on the remote machine.

        :param command: The shell command to execute.
        :return: The command's output.
        """
        try:
            # Create a connection to the remote client
            connection = Connection(
                host=self.hostname,
                user=self.user,
                connect_kwargs={"password": self.password},
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
    # Create a RemoteClient instance
    client = RemoteClient(SSH_HOST, SSH_USER, SSH_PASS, SSH_PORT)

    num_jobs = client.run_command("squeue -h | wc -l")

    # Start the Prometheus metrics server
    start_http_server(8000)

    # Create a Prometheus gauge
    jobs_gauge = Gauge("slurm_jobs", "Number of jobs in the Slurm queue")

    while True:
        # Set the gauge to the number of jobs in the Slurm queue
        jobs_gauge.set(int(num_jobs))

        # Sleep for 10 seconds
        time.sleep(60)