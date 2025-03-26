import time
import requests

SERVERS = {
    "server1": "http://localhost:5000/metrics",
    "server2": "http://localhost:5001/metrics",
    "server3": "http://localhost:5002/metrics"
}

while True:
    for name, url in SERVERS.items():
        try:
            resp = requests.get(url, timeout=2)
            data = resp.json()
            print(f"{name} - CPU idle: {data['cpu_idle']}, Memory idle: {data['memory_idle']}, Tasks: {data['tasks_in_progress']}")
        except Exception as e:
            print(f"Error reaching {name}: {e}")
    time.sleep(1)
