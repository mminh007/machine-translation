import subprocess
import time
from pyngrok import ngrok
import argparse

def main(ngrok_token=None):
    if ngrok_token:
        ngrok.set_auth_token(ngrok_token)
        print("Ngrok authentication token set.")

    # Start ngrok tunnels
    api_tunnel = ngrok.connect(5000, "http", bind_tls=True)
    #print(f"API Tunnel URL: {api_tunnel.public_url}")

    streanlit_tunnel = ngrok.connect(8501, "http", bind_tls=True)
    print(f"Streamlit Tunnel URL: {streanlit_tunnel.public_url}")
    time.sleep(5)

    fastapi_process = subprocess.Popen(
        ["python", "backend/main.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    time.sleep(2)

    streamlit_process = subprocess.Popen(
        ["streamlit", "run", "frontend/main.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    try:
        print("FastAPI and Streamlit are running... Press Ctrl+C to stop.")
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
    parser.add_argument("--ngrok-token", type=str, default=None, help="Ngrok authentication token.")
    args = parser.parse_args()

    main(args.ngrok_token)