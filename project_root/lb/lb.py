import requests
import time

servers = ["http://server1:5000", "http://server2:5000", "http://server3:5000"]
log_file = "load_balancer.log"

def get_server_load(server):
    try:
        response = requests.get(f"{server}/metrics", timeout=2)
        data = response.json()
        score = (data['cpu_idle'] + data['memory_idle']) / 2 - (data['tasks_in_progress'] * 5)  # Adjust score by active tasks
        return score
    except:
        return -1  # If a server fails, give it the worst score

def select_best_server():
    scores = {server: get_server_load(server) for server in servers}
    best_server = max(scores, key=scores.get)  # Select highest score
    with open(log_file, "a") as log:
        log.write(f"{time.ctime()} - Server Scores: {scores}\n")
        log.write(f"{time.ctime()} - Selected: {best_server}\n\n")
    return best_server

while True:
    best_server = select_best_server()
    print(f"Redirecting to: {best_server}")
    time.sleep(5)  # Adjust as needed
