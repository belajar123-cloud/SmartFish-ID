from fastapi import FastAPI, UploadFile, File, Form
from PIL import Image
from io import BytesIO
import hashlib
import random

app = FastAPI(title="SmartFresh-ID API (Stable Demo Multi Komoditas)")

# Kelas prediksi per komoditas (bisa kamu tambah nanti)
SPECIES_CLASSES = {
    "ikan": ["segar", "kurang_segar", "tidak_layak"],
    "ayam": ["segar", "kurang_segar", "tidak_layak"],
    "daging": ["segar", "kurang_segar", "tidak_layak"],
}

@app.get("/")
def root():
    return {
        "message": "SmartFresh-ID API running. Open /health or /docs",
        "supported_species": list(SPECIES_CLASSES.keys()),
    }

@app.get("/health")
def health():
    return {
        "status": "ok",
        "mode": "stable-demo-multi",
        "species": list(SPECIES_CLASSES.keys()),
    }

def stable_predict(img_bytes: bytes, species: str):
    classes = SPECIES_CLASSES.get(species, SPECIES_CLASSES["ikan"])

    # seed stabil: hash(image_bytes + species)
    h = hashlib.sha256(img_bytes + species.encode("utf-8")).hexdigest()
    seed = int(h[:8], 16)
    rng = random.Random(seed)

    pred = rng.choice(classes)
    conf = round(rng.uniform(0.70, 0.98), 3)

    probs = {}
    rest = round((1 - conf) / (len(classes) - 1), 3)
    for c in classes:
        probs[c] = conf if c == pred else rest

    return pred, conf, probs

def recommendation(species: str, pred: str):
    if pred == "segar":
        return f"{species.upper()}: Aman digunakan. Simpan dingin dan olah segera untuk kualitas terbaik."
    if pred == "kurang_segar":
        return f"{species.upper()}: Sebaiknya segera diolah. Hindari penyimpanan lama."
    return f"{species.upper()}: Tidak layak dikonsumsi. Risiko keamanan pangan."

@app.post("/predict")
async def predict(
    file: UploadFile = File(...),
    species: str = Form("ikan"),  # default
):
    img_bytes = await file.read()

    # validasi gambar
    Image.open(BytesIO(img_bytes)).convert("RGB")

    species = species.lower().strip()
    pred, conf, probs = stable_predict(img_bytes, species)

    return {
        "species": species,
        "prediction": pred,
        "confidence": conf,
        "probabilities": probs,
        "recommendation": recommendation(species, pred),
    }
