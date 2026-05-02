from flask import Flask, render_template, request, jsonify
from ultralytics import YOLO
import numpy as np
import cv2
import threading
import base64

app = Flask(__name__)

model = YOLO("model/best.pt")
lock = threading.Lock()

CLASS_NAMES = {
    0: "apple",
    1: "cucumber",
    2: "tomato",
}


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/predict", methods=["POST"])
def predict():
    if "image" not in request.files:
        return jsonify({"error": "Файл image не найден"}), 400

    file = request.files["image"]

    if file.filename == "":
        return jsonify({"error": "Файл не выбран"}), 400

    image_bytes = file.read()
    np_arr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

    if img is None:
        return jsonify({"error": "Не удалось прочитать изображение"}), 400

    with lock:
        results = model.predict(img, conf=0.25, verbose=False)
        result = results[0]

    counts = {
        "apple": 0,
        "cucumber": 0,
        "tomato": 0,
    }

    if result.boxes is not None and result.boxes.cls is not None:
        classes = result.boxes.cls.cpu().numpy().astype(int)

        for cls_id in classes:
            name = CLASS_NAMES.get(cls_id)

            if name in counts:
                counts[name] += 1

    calculations = {
        "compote_liters": round(counts["apple"] * 0.15, 2),
        "cucumber_jars": round(counts["cucumber"] * 0.1, 2),
        "tomato_jars": round(counts["tomato"] * 0.2, 2),
    }

    annotated_img = result.plot()

    ok, buffer = cv2.imencode(".jpg", annotated_img)

    if not ok:
        return jsonify({"error": "Не удалось закодировать изображение"}), 500

    image_base64 = base64.b64encode(buffer).decode("utf-8")

    return jsonify({
        "image": image_base64,
        "counts": counts,
        "calculations": calculations,
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
