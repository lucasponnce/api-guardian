import requests
import time
import random
import argparse

API_URL = "http://localhost:8000"
IPS_SIMULADAS = [f"192.168.1.{i}" for i in range(1, 21)]
IP_HEADER = "X-Forwarded-For"

def register_user(username, password):
    url = f"{API_URL}/register"
    headers = {IP_HEADER: random.choice(IPS_SIMULADAS)}
    payload = {"username": username, "password": password}

    try:
        response = requests.post(url, json=payload, headers=headers)
        print(f"[REGISTER] {username} -> {response.status_code}")
        return response
    except requests.RequestException as error:
        print(f"[ERROR] Register failed for {username}: {error}")
        return None

def login(username, password):
    url = f"{API_URL}/login"
    headers = {IP_HEADER: random.choice(IPS_SIMULADAS)}
    payload = {"username": username, "password": password}

    try:
        response = requests.post(url, data=payload, headers=headers)
        if response.status_code == 200:
            print(f"[LOGIN] {username} -> OK")
            return response.json().get("access_token")
        print(f"[LOGIN] {username} -> {response.status_code}")
    except requests.RequestException as error:
        print(f"[ERROR] Login failed for {username}: {error}")

    return None

def get_profile(token):
    url = f"{API_URL}/me"
    headers = {
        IP_HEADER: random.choice(IPS_SIMULADAS),
        "Authorization": f"Bearer {token}"
    }

    try:
        response = requests.get(url, headers=headers)
        print(f"[PROFILE] -> {response.status_code}")
        return response
    except requests.RequestException as error:
        print(f"[ERROR] Profile request failed: {error}")
        return None

def health_check():
    url = f"{API_URL}/db-check"
    headers = {IP_HEADER: random.choice(IPS_SIMULADAS)}

    try:
        response = requests.get(url, headers=headers)
        print(f"[HEALTH] -> {response.status_code}")
        return response
    except requests.RequestException as error:
        print(f"[ERROR] Health check failed: {error}")
        return None

def simulate(num_users, duration, rpm):
    users_list = []
    tokens = []
    new_user_counter = num_users + 1

    # Registramos usuarios
    print(f"[SIMULATION] Registering {num_users} users...")
    for i in range(1, num_users + 1):
        username = f"user_{i}"
        register_user(username, "pass123")
        users_list.append(username)

    # Logeamos a todos
    print(f"[SIMULATION] Logging in {num_users} users...")
    for username in users_list:
        token = login(username, "pass123")
        if token:
            tokens.append(token)

    print(f"[SIMULATION] Starting normal traffic simulation for {duration}s at {rpm} rpm...")
    start_time = time.time()

    actions = ["login", "register", "health", "profile"]
    probabilities = [40, 10, 20, 30]

    while time.time() - start_time < duration:
        action = random.choices(actions, weights=probabilities)[0]

        if action == "login":
            username = random.choice(users_list)
            token = login(username, "pass123")
            if token:
                # Mantenemos solo los últimos 50 tokens para no acumular
                tokens.append(token)
                if len(tokens) > 50:
                    tokens.pop(0)

        elif action == "register":
            username = f"user_{new_user_counter}"
            response = register_user(username, "pass123")
            if response and response.status_code == 200:
                users_list.append(username)
                new_user_counter += 1

        elif action == "health":
            health_check()

        elif action == "profile":
            if tokens:
                user_token = random.choice(tokens)
                get_profile(user_token)

        sleep_time = (60 / rpm) * random.uniform(0.5, 1.5)
        time.sleep(sleep_time)

    print(f"[SIMULATION] Done. Total users: {len(users_list)}, tokens: {len(tokens)}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Normal traffic simulator")
    parser.add_argument("--api-url", default=API_URL)
    parser.add_argument("--num-users", type=int, default=50)
    parser.add_argument("--duration", type=int, default=300, help="Duration in seconds")
    parser.add_argument("--rpm", type=int, default=60, help="Requests per minute")
    args = parser.parse_args()

    API_URL = args.api_url
    simulate(args.num_users, args.duration, args.rpm)
