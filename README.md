# :earth_asia: Machine Translation System (Text & Voice)

A multilingual translation system that supports both text and speech input, built using **FastAPI** for the backend and **Streamlit** for the frontend. The system leverages pretrained models and containerized services to provide real-time translation capabilities.

---

## Project structure
```
#bash
machine-translator/
├── src/                    # Main source code
│ ├── agents/               # LangChain / RAG agents
│ ├── backend/              # FastAPI app
│ ├── client/               # Frontend-to-backend request handler
│ ├── core/                 # Core logic (translation, TTS, STT)
│ ├── schema/               # Pydantic models
│ ├── streamlit_app.py      # Streamlit UI app
│ └── ...
├── vlm_api/                # Vision-language model APIs
├── docker-compose.yaml     # Docker orchestration config
├── frontend.dockerfile     # Dockerfile for Streamlit UI
├── entrypoint.sh           # Entrypoint script
├── app_ngrok.py            # Ngrok tunnel (for local deploy)
├── .env                    # Environment variables
├── requirements.txt        # Python dependencies
├── Makefile                # Optional command shortcuts
└── README.md               # This file
---
```

---

## 🚀 Quick Start (Using Docker)

### 🔗 Clone the repository

```bash
git clone https://github.com/mminh007/machine-translation.git
cd machine-translation
---
```


### ⚙️ **Create a `.env` file**

In the root the directory create a `.env` file

```
# .env file
NGROK_TOKEN=your_ngrok_token_here
VLLM_API_KEY=your_VLLM_API_KEY_here
HUGGINGFACE_TOKEN=your_HUGGINGFACE_TOKEN_here
---
```

:key: **You can get your HuggingFace token from:** https://huggingface.co/settings/tokens

:key: `VLLM_API_KEY` is the key used when running the `vllm_api` service.
The default value is `paos2025`.

---

### 👀 Create docker network
Before running the services, create a dedicated Docker network to ensure that containers can communicate with each other seamlessly.

```
docker network create paos-network
```
This command creates a custom network named paos-network, which will be used to connect the `frontend`, `backend`, and `vllm_api` services.

---

### :running: Build and run Fontend - Backend:

```
# bash
docker-compose up --build
---
```

---

### 👀 Download model architecture:
Run file `download_pretrained.ipynb`

📄 About `download_pretrained.ipynb`:
-   This notebook is responsible for
  
-   Loading your Hugging Face API token securely via .env

-   Authenticating with the Hugging Face Hub

-   Downloading the meta-llama/Llama-3.2-1B-Instruct model using snapshot_download

-   Printing the local path where the model is saved

---

### :running: Run vLLM API Service:
This step is for enabling **local LLM inference** via a dedicated API service. If your application needs to use LLMs (e.g. chat, summarization, intent detection, etc.), the vlm_api service provides a containerized backend for that.

To start the LLM service locally:

```
# bash
cd ./vllm_api
docker-compose up --build
---
```

This will:

-   Launch the vLLM API server on port `8001`

-   Make it accessible via `http://vllm_api:8001` within the Docker network

-   Allow the backend service to make requests to the LLM engine without relying on external APIs

✅ **Preconfigured Models**: 
The project also supports the integration of the following paid models:

| Model Name |	Description |
| --- | ------------ |
| gpt-4o | OpenAI’s GPT-4 Omni |
| gpt-4o-mini |	Lightweight GPT-4o variant |
| azure-gpt-4o | GPT-4o via Microsoft Azure API |
| azure-gpt-4o-mini | Mini GPT-4o via Azure |
| deepseek-chat | Open-source LLM by DeepSeek |
	
These models require an **API key** to be configured in the `.env` file.
For details on the parameters, refer to the file: `/core/settings.py`.
	
---

## :globe_with_meridians: Access the Web App

After starting all services, open your browser and go to:

```
http://localhost:8501
---
```

---

## :hammer: NOTE: Useful Docker Commands

| Command |	Description |
| --- | ------------ |
| `docker-compose up` |	Start core services (frontend, backend) |
| `cd vlm_api && docker-compose up` | Start the vLLM API service |
| `docker-compose down` | Stop and remove containers |
| `docker-compose build` | Build Docker images |
| `docker-compose logs -f` |	View logs in real time |

---

## :raised_hands: Acknowledgments:

- Langchain
- Langgraph
- Streamlit
- FastAPI
- vLLM
