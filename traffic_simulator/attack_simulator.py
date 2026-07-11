import requests
import time
from normal_traffic import API_URL, IP_HEADER
import random
import argparse

# IPS_SIMULADAS = [f"192.168.1.{i}" for i in range(1, 21)]

def brute_force_attack(username, attempts=50):
    url = f"{API_URL}/login"
    attacker_ip = "10.0.0.99" # Definimos una IP fija
    headers = {IP_HEADER: attacker_ip}

    for i in range(attempts):
        fake_password = f"fakepass{i}"
        payload = {"username": username, "password": fake_password}
        response = requests.post(url, data=payload, headers=headers)
        print(f"[BRUTEFORCE] attempt {i + 1} -> {response.status_code}")
        time.sleep(0.1) # Rápido a propósito, simulando una máquina/bot

def scraping_attack(max_id_attempts=100):
    attacker_ip = "10.0.0.101"
    headers = {IP_HEADER: attacker_ip}

    for user_id in range(1, max_id_attempts + 1):
        url = f"{API_URL}/users/{user_id}"
        response = requests.get(url, headers=headers)
        print(f"[SCRAPING] /users/{user_id} -> {response.status_code}")
        time.sleep(0.05)

def endpoint_fuzzing_attack(attempts=30):
    attacker_ip = "10.0.0.102"
    headers = {IP_HEADER: attacker_ip}
    common_paths = ["/admin", "/api/v1", "/api/users", "/backup", "/.env", "/config", "/debug", "/wp-admin", "/.git"]

    for i in range(attempts):
        path = random.choice(common_paths)
        url = f"{API_URL}{path}"
        response = requests.get(url, headers=headers)
        print(f"[FUZZING] {path} -> {response.status_code}")
        time.sleep(0.1)