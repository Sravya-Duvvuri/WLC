from flask import Flask, jsonify, request
import time, random, os, threading

app = Flask(__name__)

tasks_in_progress = 0
cpu_load = 0  # Dynamic CPU load
memory_load = 0  # Dynamic memory load
buffer = []  # Task buffer
lock = threading.Lock()

# Read delay ranges from environment variables
DELAY_MIN = float(os.getenv("PROCESSING_DELAY_MIN", 10))
DELAY_MAX = float(os.getenv("PROCESSING_DELAY_MAX", 15))

@app.route('/work', methods=['POST'])
def work():
    global tasks_in_progress, cpu_load, memory_load, buffer
    
    with lock:
        cpu_idle = max(100 - cpu_load, 0)
        memory_idle = max(100 - memory_load, 0)
        
        # If the server is overloaded, buffer the task
        if cpu_idle < 20 or memory_idle < 20:
            buffer.append(time.time())  # Store task timestamp
            return jsonify({"message": "Server overloaded, task buffered."}), 503

        tasks_in_progress += 1
        cpu_load += random.uniform(8, 12)
        memory_load += random.uniform(6, 10)
    
    processing_time = random.uniform(DELAY_MIN, DELAY_MAX)
    time.sleep(processing_time)
    
    with lock:
        tasks_in_progress -= 1
        cpu_load = max(cpu_load - random.uniform(3, 6), 0)
        memory_load = max(memory_load - random.uniform(2, 5), 0)
    
    return jsonify({"message": "Task completed", "processing_time": processing_time})

@app.route('/metrics')
def metrics():
    global tasks_in_progress, cpu_load, memory_load
    with lock:
        tasks = tasks_in_progress
        cpu_idle = max(100 - cpu_load, 0)
        memory_idle = max(100 - memory_load, 0)
    
    return jsonify({
        "cpu_idle": round(cpu_idle, 2),
        "memory_idle": round(memory_idle, 2),
        "tasks_in_progress": tasks,
        "buffer_size": len(buffer)  # Monitor buffered tasks
    })

# Background thread to process buffered tasks

def process_buffer():
    global buffer, tasks_in_progress, cpu_load, memory_load
    while True:
        with lock:
            cpu_idle = max(100 - cpu_load, 0)
            memory_idle = max(100 - memory_load, 0)

            if buffer and cpu_idle > 70 and memory_idle > 70:
                buffer.pop(0)  # Remove task from buffer
                tasks_in_progress += 1
                cpu_load += random.uniform(8, 12)
                memory_load += random.uniform(6, 10)
        
        time.sleep(1)  # Check buffer every second

if __name__ == '__main__':
    threading.Thread(target=process_buffer, daemon=True).start()
    app.run(host='0.0.0.0', port=5000)
