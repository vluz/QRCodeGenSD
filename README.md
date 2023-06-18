# QR Code Gen with Stable Diffusion
### A gradio app that uses a stable diffusion model to generate novel QR codes

**Takes a long time to run the first time as it has to download a large amount of files**

This is a hevily modified version of the offician HF app.

Focus has been put into adding a useful model, 
<br>
modifying pipe for low vram use and clean up the interface.

<hr>

Open a command prompt and `cd` to a new directory of your choosing:

Create a virtual environment with:
```
python -m venv "venv"
venv\Scripts\activate
```

To install do:
```
git clone https://github.com/vluz/QRCodeGenSD.git
cd QRCodeGenSD
pip install -r requirements.txt
```

To run do:<br>
```
python qrgen.py
``` 

App run on a browser at http://127.0.0.1:7860

To exit the virtual environment do:
```
venv\Scripts\deactivate
```

<hr>

Example outputs:
