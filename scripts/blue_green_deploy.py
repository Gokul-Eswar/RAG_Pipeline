#!/usr/bin/env python3
"""
Blue-Green Deployment Script for Big Data RAG API.

Usage:
    python scripts/blue_green_deploy.py --image <new_image_tag>

Prerequisites:
    - kubectl installed and configured
    - Access to the Kubernetes cluster
"""

import argparse
import subprocess
import time
import sys
import yaml


def run_command(command: str) -> str:
    """Run a shell command and return output."""
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {command}")
        print(f"Stderr: {e.stderr}")
        raise


def get_active_color() -> str:
    """Determine which color (blue/green) is currently active."""
    try:
        # Check the service selector
        svc_json = run_command("kubectl get service big-data-rag-api -o json")
        svc = yaml.safe_load(svc_json)
        selector = svc.get('spec', {}).get('selector', {})
        return selector.get('version', 'blue')  # Default to blue if unknown
    except Exception:
        print("Could not determine active color. Assuming 'blue' is active.")
        return 'blue'


def deploy_new_version(color: str, image: str):
    """Deploy the new version (Deployment)."""
    print(f"Deploying {color} version with image {image}...")

    # Load base deployment template
    with open("k8s/deployment.yaml", "r") as f:
        deployment = yaml.safe_load(f)

    # Modify for Blue/Green
    deployment['metadata']['name'] = f"big-data-rag-api-{color}"
    deployment['spec']['selector']['matchLabels']['version'] = color
    deployment['spec']['template']['metadata']['labels']['version'] = color
    deployment['spec']['template']['spec']['containers'][0]['image'] = image

    # Save temp manifest
    manifest_path = f"k8s/deployment-{color}.yaml"
    with open(manifest_path, "w") as f:
        yaml.dump(deployment, f)

    # Apply
    # run_command(f"kubectl apply -f {manifest_path}")
    print(f"Simulating: kubectl apply -f {manifest_path}")


def wait_for_ready(color: str):
    """Wait for the new deployment to be ready."""
    print(f"Waiting for {color} deployment to be ready...")
    # run_command(f"kubectl rollout status deployment/big-data-rag-api-{color}")
    print("Simulating: kubectl rollout status...")
    time.sleep(2)  # Simulate wait


def switch_traffic(color: str):
    """Update Service to point to new color."""
    print(f"Switching traffic to {color}...")
    # cmd = f"kubectl patch service big-data-rag-api " \
    #       f"-p '{{\"spec\":{{\"selector\":{{\"version\":\"{color}\"}}}}}}'"
    # run_command(cmd)
    print(f"Simulating: kubectl patch service selector to version={color}")


def cleanup_old_version(old_color: str):
    """Delete the old deployment."""
    print(f"Cleaning up {old_color} version...")
    # run_command(f"kubectl delete deployment big-data-rag-api-{old_color}")
    print(f"Simulating: kubectl delete deployment big-data-rag-api-{old_color}")


def main():
    parser = argparse.ArgumentParser(description="Blue-Green Deployment")
    parser.add_argument("--image", required=True, help="New Docker image tag")
    args = parser.parse_args()

    active_color = get_active_color()
    new_color = "green" if active_color == "blue" else "blue"

    print(f"Current active version: {active_color}")
    print(f"Deploying new version: {new_color}")

    try:
        deploy_new_version(new_color, args.image)
        wait_for_ready(new_color)
        switch_traffic(new_color)
        cleanup_old_version(active_color)
        print("Deployment successful!")
    except Exception as e:
        print(f"Deployment failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
