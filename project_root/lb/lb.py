import time
import logging
from threading import Thread
import requests
import random

# Configure logging to output to both file and console
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("loadbalancer.log"), logging.StreamHandler()]
)

# Define internal server details (using Docker service names)
SERVERS = [
    {"name": "server1", "url": "http://server1:5000/metrics", "work_url": "http://server1:5000/work"},
    {"name": "server2", "url": "http://server2:5000/metrics", "work_url": "http://server2:5000/work"},
    {"name": "server3", "url": "http://server3:5000/metrics", "work_url": "http://server3:5000/work"},
]

def get_server_load(server):
    """
    Fetch /metrics from a server and compute its score.
    New score formula: (cpu_idle + memory_idle)/2 - (tasks_in_progress * 3)
    A higher score indicates more available capacity.
    """
    try:
        response = requests.get(server["url"], timeout=2)
        if response.status_code == 200:
            data = response.json()
            cpu_idle = data.get("cpu_idle", 0)
            memory_idle = data.get("memory_idle", 0)
            tasks = data.get("tasks_in_progress", 0)
            score = (cpu_idle + memory_idle) / 2 - (tasks * 3)
            return score
        else:
            logging.warning(f"{server['name']} returned status code {response.status_code}.")
            return float("-inf")
    except requests.exceptions.RequestException as e:
        logging.error(f"{server['name']} unreachable. Error: {e}")
        return float("-inf")

def select_server():
    """
    Compute scores for all servers and select the one with the highest score.
    If servers are nearly equal (within a threshold), choose randomly among them.
    """
    server_scores = {}
    for server in SERVERS:
        score = get_server_load(server)
        server_scores[server["name"]] = score
        logging.info(f"{server['name']}: Score = {score:.2f}")
    
    best_score = max(server_scores.values())
    threshold = 0.5  # Adjust as needed for tie-breaking
    best_servers = [name for name, s in server_scores.items() if abs(s - best_score) < threshold]
    chosen = random.choice(best_servers) if best_servers else max(server_scores, key=server_scores.get)
    logging.info(f"Selected {chosen} (Score: {server_scores[chosen]:.2f})")
    return chosen

def simulate_requests():
    """
    Continuously select the best server and send a request to its /work endpoint.
    Increased timeout to 15 seconds to handle longer processing delays.
    """
    while True:
        chosen_name = select_server()
        target = next((s for s in SERVERS if s["name"] == chosen_name), None)
        if not target:
            logging.error("No matching server found. Retrying...")
            time.sleep(1)
            continue

        try:
            logging.info(f"Sending request to {chosen_name} at {target['work_url']}")
            response = requests.get(target["work_url"], timeout=15)
            if response.status_code == 200:
                logging.info(f"Response from {chosen_name}: {response.json()}")
            else:
                logging.warning(f"{chosen_name} returned status {response.status_code} on /work")
        except requests.exceptions.RequestException as e:
            logging.error(f"Error reaching {chosen_name}: {e}")
        
        time.sleep(random.uniform(0.5, 1.5))

if __name__ == "__main__":
    logging.info("Starting load balancer...")
    t = Thread(target=simulate_requests, daemon=True)
    t.start()
    # Keep the main thread alive indefinitely.
    while True:
        time.sleep(10)
