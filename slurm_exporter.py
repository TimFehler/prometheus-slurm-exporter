import os
import requests
from fabric import Connection
import time
from prometheus_client import start_http_server, Gauge

class RemoteClient:
    def __init__(self, hostname: str, user: str, port: int, timeout: int = 600):
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
        self.timeout = timeout # timeout in seconds, default is 10 minutes

        self.connection = Connection(
            host=self.hostname,
            user=self.user,
            connect_kwargs={"key_filename": self.key},
            port=self.port,
            connect_timeout=self.timeout # connection timeout without activity
        )

    def open(self):
        """
        Reopen the connection to the remote machine.
        """
        try:
           self.connection.open()
        except Exception as e:
            print(f"An error occurred: {str(e)}")

    def close(self):
        """
        Disconnect from the remote machine.
        """
        try:
            self.connection.close()
        except Exception as e:
            print(f"An error occurred: {str(e)}")

    def run_command(self, command: str) -> str:
        """
        Run a command on the remote machine.

        :param command: The shell command to execute.
        :return: The command's output.
        """
        # Run the command and capture the result
        result = self.connection.run(f"bash -lc '{command}'", hide=True)

        return result.stdout.strip()

class Timer():
    def __init__(self):
        self.start_time = time.time()

    def reset(self):
        self.start_time = time.time()

    def elapsed(self):
        return time.time() - self.start_time

if __name__ == "__main__":
    # Get the SSH connection details from environment variables
    SSH_HOST = os.environ.get('SLURM_SSH_HOST')
    SSH_USER = os.environ.get('SLURM_SSH_USER')
    SSH_PORT = os.environ.get('SLURM_SSH_PORT')
    SSH_TIMEOUT = int(os.environ.get('SLURM_SSH_TIMEOUT')) # timeout in seconds, default is 10 minutes

    SCRAPE_INTERVAL = int(os.environ.get('SCRAPE_INTERVAL'))

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

    server_thread_count_gauge = Gauge("slurm_server_thread_count", "Number of threads in the Slurm controller")
    server_agent_queue_size_gauge = Gauge("slurm_server_agent_queue_size", "Size of the Slurm controller agent queue")

    length_schedule_cycle_last_gauge = Gauge("slurm_length_schedule_cycle_last", "Length of the last scheduling cycle in milliseconds")
    length_schedule_cycle_avg_gauge = Gauge("slurm_length_schedule_cycle_avg", "Average length of scheduling cycles in milliseconds")

    duration_of_current_SSH_session_gauge = Gauge("duration_of_current_SSH_session", "Duration of current SSH session in seconds")

    # Create a RemoteClient instance
    client = RemoteClient(SSH_HOST, SSH_USER, SSH_PORT, SSH_TIMEOUT)
    mytimer = Timer()

    # Continuously update the Prometheus gauges
    while True:
        # Check if still connected, if not establish a connection
        if not client.connection.is_connected:
            client.open()
            mytimer.reset()

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

        server_thread_count = client.run_command("sdiag | grep -m 1 Server\ thread\ count | awk {print\ \$4}")
        server_thread_count_gauge.set(int(server_thread_count))

        server_agent_queue_size = client.run_command("sdiag | grep -m 1 Agent\ queue\ size | awk {print\ \$4}")
        server_agent_queue_size_gauge.set(int(server_agent_queue_size))

        length_schedule_cycle_last = client.run_command("sdiag | grep -m 1 Last\ cycle | awk {print\ \$3}")
        length_schedule_cycle_last_gauge.set(float(length_schedule_cycle_last))

        length_schedule_cycle_avg = client.run_command("sdiag | grep -m 1 Mean\ cycle | awk {print\ \$3}")
        length_schedule_cycle_avg_gauge.set(float(length_schedule_cycle_avg))

        duration_of_current_SSH_session_gauge.set(mytimer.elapsed())

        # Force reconnection if the duration of the current SSH session exceeds the timeout
        # This ensures that the connection does not block the remote machine indefinitely
        if mytimer.elapsed() >= client.timeout:
            client.close()

        time.sleep(SCRAPE_INTERVAL)
