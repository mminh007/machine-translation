# :earth_asia: machine-translation

A real-time translation app for both speech and text using FastAPI, Streamlit, and Facebook AI’s MBart model.

## :rocket: Features
:microphone: Translate speech (audio) between Vietnamese ↔ English

:memo: Translate text between Vietnamese ↔ English

:robot: Powered by facebook/mbart-large-50-many-to-many-mmt

:globe_with_meridians: Access remotely using ngrok

---
## :gear: Installation:

:point_right: **Clone the repository:**

```
# bash
git clone https://github.com/mminh007/machine-translation.git
cd machine-translation
```

:point_right: **Install dependencies**

```
# bash
pip install -r requirements.txt
```

:point_right: **Create a `.env` file**
In the root the directory create a `.env` file and add your **Ngrok token**

```
# env
NGROK_TOKEN=your_ngrok_token_here
```
:key: **You can get your token from:** https://dashboard.ngrok.com/get-started/your-authtoken

---

## :running: Run the App:

```
# bash
python all.py
```

This will:
-   Start FastAPI backend on port `8000`
-   Start Streamlit frontend on port `8501`
-   Create Ngrok tunnels and show public URLs for both.

---

## :globe_with_meridians: Public URLs Example

Once running, you will see output like:

```
ngnix
API Tunnel URL: https://xxxxx.ngrok.io
Streamlit Tunnel URL: https:yyyyy.ngrok.io
```
Open the Streamlit in your browser to use the app.

---
## :hammer: NOTE:

-   Make sure your microphone works for speech input
-   The first load might take time while loading the `mbar` model.
-   You can customize source/target languages via dropdowns in the UI.

---

## :raised_hands: Acknowledgments:
-   HuggingFace Transformers
-   Streamlit
-   FastAPI
-   PyNgrok
-   SpeechRecognition (Google API)