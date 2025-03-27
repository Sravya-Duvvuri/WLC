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

# Dictionary to track each server's state (1 = available, 0 = unavailable)
server_states = { server["name"]: 1 for server in SERVERS }
# Thresholds for state change
UNAVAILABLE_THRESHOLD = 20    # Below this, server is marked unavailable (state 0)
AVAILABLE_THRESHOLD = 70      # At or above this, server is marked available (state 1)

# Simple in-memory task buffer
task_buffer = []

def get_server_metrics(server):
    """
    Fetch /metrics from a server.
    Returns a dictionary with cpu_idle, memory_idle, and tasks_in_progress,
    or None if unreachable.
    """
    try:
        response = requests.get(server["url"], timeout=2)
        if response.status_code == 200:
            return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"{server['name']} unreachable. Error: {e}")
    return None

def update_server_state():
    """
    Update server_states based on the latest metrics.
    If either cpu_idle or memory_idle is below UNAVAILABLE_THRESHOLD, mark as unavailable (0).
    If both are at or above AVAILABLE_THRESHOLD, mark as available (1).
    """
    global server_states
    for server in SERVERS:
        metrics = get_server_metrics(server)
        if metrics is not None:
            cpu_idle = metrics.get("cpu_idle", 0)
            memory_idle = metrics.get("memory_idle", 0)
            if cpu_idle < UNAVAILABLE_THRESHOLD or memory_idle < UNAVAILABLE_THRESHOLD:
                server_states[server["name"]] = 0
            elif cpu_idle >= AVAILABLE_THRESHOLD and memory_idle >= AVAILABLE_THRESHOLD:
                server_states[server["name"]] = 1
            logging.info(f"{server['name']} state updated: {server_states[server['name']]} (CPU idle: {cpu_idle}, Memory idle: {memory_idle})")
        else:
            server_states[server["name"]] = 0
            logging.info(f"{server['name']} state updated: 0 (unreachable)")

def compute_server_score(metrics):
    """
    Compute a score from metrics.
    Formula: (cpu_idle + memory_idle)/2 - (tasks_in_progress * 3)
    A higher score indicates more available capacity.
    """
    cpu_idle = metrics.get("cpu_idle", 0)
    memory_idle = metrics.get("memory_idle", 0)
    tasks = metrics.get("tasks_in_progress", 0)
    score = (cpu_idle + memory_idle) / 2 - (tasks * 3)
    return score

def select_server():
    """
    Query all available servers (state 1), compute their scores,
    and select the server with the highest score. If no server is available, return None.
    """
    update_server_state()  # Refresh states
    available_servers = []
    server_scores = {}
    
    for server in SERVERS:
        if server_states.get(server["name"], 0) == 1:
            metrics = get_server_metrics(server)
            if metrics is not None:
                score = compute_server_score(metrics)
                server_scores[server["name"]] = score
                available_servers.append(server["name"])
                logging.info(f"{server['name']}: Score = {score:.2f}")
            else:
                server_states[server["name"]] = 0
    if not available_servers:
        logging.error("No available servers. All servers are overloaded!")
        return None
    best_score = max(server_scores.values())
    threshold = 0.5  # For tie-breaking
    best_servers = [name for name, s in server_scores.items() if abs(s - best_score) < threshold]
    chosen = random.choice(best_servers) if best_servers else max(server_scores, key=server_scores.get)
    logging.info(f"Selected {chosen} (Score: {server_scores[chosen]:.2f})")
    return chosen

def simulate_requests():
    """
    Continuously select the best available server and send a POST request to its /work endpoint.
    If no server is available, buffer the task and log that a new server is needed.
    Also process any buffered tasks when an available server is found.
    """
    global task_buffer
    while True:
        chosen_name = select_server()
        if chosen_name is None:
            logging.error("All servers overloaded. Buffering task and indicating need for new server.")
            task_buffer.append({"timestamp": time.time()})
            logging.error("New server needed to handle the load!")
            time.sleep(2)
            continue
        
        # If there are buffered tasks and the chosen server is healthy, process them
        if task_buffer:
            logging.info(f"Processing {len(task_buffer)} buffered tasks on {chosen_name}.")
            task_buffer.clear()  # In a real system, dequeue and process individually.
        
        target = next((s for s in SERVERS if s["name"] == chosen_name), None)
        if not target:
            logging.error("No matching server found. Retrying...")
            time.sleep(1)
            continue

        try:
            logging.info(f"Sending request to {chosen_name} at {target['work_url']} (POST)")
            response = requests.post(target["work_url"], timeout=15)
            if response.status_code == 200:
                logging.info(f"Response from {chosen_name}: {response.json()}")
            else:
                logging.warning(f"{chosen_name} returned status {response.status_code} on /work")
                # Buffer the task for retry if not successful
                task_buffer.append({"timestamp": time.time()})
        except requests.exceptions.RequestException as e:
            logging.error(f"Error reaching {chosen_name}: {e}")
            # Buffer the task if a timeout or any request exception occurs
            task_buffer.append({"timestamp": time.time()})
        
        time.sleep(random.uniform(0.5, 1.5))

if __name__ == "__main__":
    logging.info("Starting load balancer with server state management and buffering...")
    t = Thread(target=simulate_requests, daemon=True)
    t.start()
    # Keep the main thread alive indefinitely
    while True:
        time.sleep(10)
