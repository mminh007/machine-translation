import subprocess
import time
from pyngrok import ngrok
import argparse
from dotenv import load_dotenv
import requests
import os

def wait_for_server(url, timeout=70):
    print(f"⏳ Waiting for server at {url} to start...")
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(url)
            if response.status_code == 200:
                print("✅ Server is up!")
                return True
        except:
            pass
        time.sleep(1)
    print("❌ Timeout: Server did not start in time.")
    return False


def main(ngrok_token=None):

    if ngrok_token is None:
        try:
            load_dotenv()  # Load .env file if present
            ngrok_token = os.getenv("NGROK_TOKEN")

            ngrok.set_auth_token(ngrok_token)
            print("Ngrok authentication token set.")

        except Exception as e:
            print(f"❌ Error loading ngrok token: {e}")
            print("❌ Please provide the ngrok token as an argument or set it in the .env file.")
            return
    else:
        ngrok.set_auth_token(ngrok_token)
        print("Ngrok authentication token set.")

    print("🏃 Starting FastAPI backend...")
    fastapi_process = subprocess.Popen(
        ["python", "backend/main.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    if not wait_for_server("http://localhost:8000/docs"):
        fastapi_process.terminate()
        return
    
    # Start ngrok tunnels
    api_tunnel = ngrok.connect(8000, "http", bind_tls=True)
    print(f"🚀 API Tunnel URL: {api_tunnel.public_url}")
    time.sleep(5)
    
    print("🏃 Starting Streamlit frontend...")
    streamlit_process = subprocess.Popen(
        ["streamlit", "run", "frontend/main.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    streanlit_tunnel = ngrok.connect(8501, "http", bind_tls=True)

    print(f"🌏 Streamlit Tunnel URL: {streanlit_tunnel.public_url}")

    
    try:
        print("⚠️ FastAPI and Streamlit are running... Press Ctrl+C to stop.")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping processes...")
        fastapi_process.terminate()
        streamlit_process.terminate()
        ngrok.kill()
        print("Processes stopped.")



if __name__ == "__main__":    

    parser = argparse.ArgumentParser(description="Run FastAPI and Streamlit with ngrok tunnels.")
    parser.add_argument("--ngrok-token", type=str, default=None, help=argparse.SUPPRESS)
    args = parser.parse_args()

    main(args.ngrok_token)