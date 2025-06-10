import subprocess
import time
from pyngrok import ngrok
import argparse
from dotenv import load_dotenv
import requests
import os

load_dotenv()


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


def main(args):
    ngrok_token = os.getenv("NGROK_TOKEN")

    if not ngrok_token:
        print("❌ Please set NGROK_TOKEN in .env file or environment.")
        return

    ngrok.set_auth_token(ngrok_token)
    print("✅ Ngrok token loaded.")

    if not args.no_backend:
        print("🏃 Starting FastAPI backend...")
        fastapi_process = subprocess.Popen(
            ["python", "-m", "backend.main"],
            cwd="src",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        if not wait_for_server("http://localhost:8000/docs", timeout=args.timeout):
            print("❌ FastAPI server did not start in time. Terminating process.")
            fastapi_process.terminate()
            return
        
        # Start ngrok tunnels
        api_tunnel = ngrok.connect(8000, "http", bind_tls=True)
        print(f"🚀 API Tunnel URL: {api_tunnel.public_url}")
        time.sleep(5)
    
    print("🏃 Starting Streamlit frontend...")
    streamlit_process = subprocess.Popen(
        ["streamlit", "run", "streamlit_app.py"],
        cwd="src",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    streanlit_tunnel = ngrok.connect(8501, "http", bind_tls=True)

    print(f"🌏 Streamlit Tunnel URL: {streanlit_tunnel.public_url}")

    
    try:
        print("⚠️ Application is running... Press Ctrl+C to stop.")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping processes...")
        if not args.no_backend:
            fastapi_process.terminate()
            print("FastAPI process terminated.")
        streamlit_process.terminate()
        ngrok.kill()
        print("Processes stopped.")



if __name__ == "__main__":    

    parser = argparse.ArgumentParser(description="Run FastAPI and Streamlit with ngrok tunnels.")
    parser.add_argument("--no-backend", action='store_true')
    parser.add_argument("--timeout", type=int, default=70, help="Timeout for waiting for the server to start.")
    args = parser.parse_args()

    main(args)