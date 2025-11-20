import json
import os
import time

import yaml
from metaflow import FlowSpec, IncludeFile, environment, resources, step

# Shared environment variables for all steps
COMMON_ENV = {
    "AWS_ACCESS_KEY_ID": os.getenv("AWS_ACCESS_KEY_ID", ""),
    "AWS_SECRET_ACCESS_KEY": os.getenv("AWS_SECRET_ACCESS_KEY", ""),
    "AWS_DEFAULT_REGION": "us-east-1",
}


class CityLatencyFlow(FlowSpec):

    config = IncludeFile(
        "config", help="City config", is_text=True, default="config.yaml"
    )

    @environment(vars=COMMON_ENV)
    @resources(cpu=1, memory=1024)
    @step
    def start(self):
        import yaml

        cfg = yaml.safe_load(self.config)
        print("Printing Config:")
        print(cfg)

        print("Printing Environment Variables:")
        print(f"AWS_ACCESS_KEY_ID: {os.getenv('AWS_ACCESS_KEY_ID')}")
        print(f"AWS_SECRET_ACCESS_KEY: {os.getenv('AWS_SECRET_ACCESS_KEY')}")
        print(f"AWS_DEFAULT_REGION: {os.getenv('AWS_DEFAULT_REGION')}")

        self.cities = cfg["cities"]
        self.city_list = [(c["code"], c["num"]) for c in self.cities]
        self.next(self.process_city, foreach="city_list")

    @environment(vars=COMMON_ENV)
    @resources(cpu=1, memory=2048)
    @step
    def process_city(self):
        code, num = self.input
        print(f"[{code}] starting loop up to {num}")

        start = time.time()
        for i in range(num):
            print(f"[{code}] i = {i}")
            time.sleep(1)

        elapsed = round(time.time() - start, 2)
        self.result = {"city": code, "latency_seconds": elapsed}
        self.next(self.join_results)

    @environment(vars=COMMON_ENV)
    @resources(cpu=1, memory=2048)
    @step
    def join_results(self, inputs):
        latencies = {
            inp.result["city"]: inp.result["latency_seconds"] for inp in inputs
        }
        self.latencies = latencies
        print("Aggregated latencies:", latencies)
        self.next(self.end)

    @environment(vars=COMMON_ENV)
    @resources(cpu=1, memory=2048)
    @step
    def end(self):
        print("Final latencies:", self.latencies)
        with open("latencies.json", "w") as f:
            json.dump(self.latencies, f)
        print("Wrote latencies.json")

        import os

        import boto3

        print("Environment Variables:")
        print(os.getenv("METAFLOW_S3_ENDPOINT_URL"))
        print(os.getenv("AWS_ACCESS_KEY_ID"))
        print(os.getenv("AWS_SECRET_ACCESS_KEY"))
        print(os.getenv("AWS_DEFAULT_REGION"))
        print(
            "Uploading latencies.json to s3://metaflow/city-latency-demo-bucket/latencies.json"
        )
        s3 = boto3.client("s3", endpoint_url=os.getenv("METAFLOW_S3_ENDPOINT_URL"))
        s3.upload_file(
            "latencies.json", "metaflow", "city-latency-demo-bucket/latencies.json"
        )


if __name__ == "__main__":
    CityLatencyFlow()
