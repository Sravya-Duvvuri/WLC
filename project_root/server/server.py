from flask import Flask, jsonify
import time, random, os, threading

app = Flask(__name__)

tasks_in_progress = 0
cpu_load = 0  # Added to track dynamic CPU load
memory_load = 0  # Added to track dynamic memory load
lock = threading.Lock()

# Read delay ranges from environment variables
DELAY_MIN = float(os.getenv("PROCESSING_DELAY_MIN", 10))
DELAY_MAX = float(os.getenv("PROCESSING_DELAY_MAX", 15))

@app.route('/work')
def work():
    global tasks_in_progress, cpu_load, memory_load
    processing_time = random.uniform(DELAY_MIN, DELAY_MAX)

    with lock:
        tasks_in_progress += 1
        cpu_load += random.uniform(8, 12)  # More dynamic CPU load per task
        memory_load += random.uniform(6, 10)  # More dynamic memory usage per task

    time.sleep(processing_time)

    with lock:
        tasks_in_progress -= 1
        # Introduce gradual cool-down instead of instantly resetting to 100%
        cpu_load = max(cpu_load - random.uniform(3, 6), 0)
        memory_load = max(memory_load - random.uniform(2, 5), 0)

    return jsonify({"message": "Task completed", "processing_time": processing_time})

@app.route('/metrics')
def metrics():
    global tasks_in_progress, cpu_load, memory_load
    with lock:
        tasks = tasks_in_progress
        # Dynamic idle calculation
        cpu_idle = max(100 - cpu_load, 0)
        memory_idle = max(100 - memory_load, 0)

    return jsonify({
        "cpu_idle": round(cpu_idle, 2),
        "memory_idle": round(memory_idle, 2),
        "tasks_in_progress": tasks
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
