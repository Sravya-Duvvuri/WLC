from locust import HttpUser, task, between

class LoadTestUser(HttpUser):
    wait_time = between(1, 3)  # ⬅️ Increase wait time range if needed
    @task
    def load_test(self):
        self.client.get("/work")

