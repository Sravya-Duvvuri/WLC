import time
import requests
import csv
import os

# Define servers to monitor
SERVERS = {
    "server1": "http://localhost:5000/metrics",
    "server2": "http://localhost:5001/metrics",
    "server3": "http://localhost:5002/metrics"
}

CSV_FILE = "monitor_logs.csv"

# If CSV file does not exist, create it and write headers.
if not os.path.exists(CSV_FILE):
    with open(CSV_FILE, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["timestamp", "server", "cpu_idle", "memory_idle", "tasks_in_progress"])

while True:
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    for name, url in SERVERS.items():
        try:
            resp = requests.get(url, timeout=2)
            data = resp.json()
            cpu = data.get("cpu_idle", "N/A")
            mem = data.get("memory_idle", "N/A")
            tasks = data.get("tasks_in_progress", "N/A")
            print(f"{name} - CPU idle: {cpu}, Memory idle: {mem}, Tasks: {tasks}")
            with open(CSV_FILE, "a", newline="") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow([timestamp, name, cpu, mem, tasks])
        except Exception as e:
            print(f"Error reaching {name}: {e}")
    time.sleep(1)
