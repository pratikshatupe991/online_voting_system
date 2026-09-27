import os
import sys
import logging
import warnings
import urllib.request
import ssl
import cv2
from deepface import DeepFace
import base64
import numpy as np

os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
warnings.filterwarnings("ignore")
logging.getLogger('tensorflow').setLevel(logging.FATAL)
logging.getLogger('absl').setLevel(logging.FATAL)


def silent_unraisable_hook(unraisable):
    if isinstance(unraisable.exc_value, ValueError):
        return
    sys.__unraisablehook__(unraisable)


sys.unraisablehook = silent_unraisable_hook


current_folder = os.getcwd()
os.environ["DEEPFACE_HOME"] = current_folder
weights_dir = os.path.join(current_folder, ".deepface", "weights")
os.makedirs(weights_dir, exist_ok=True)
facenet_path = os.path.join(weights_dir, "facenet_weights.h5")

if not os.path.exists(facenet_path):
    print("First time setup: Downloading AI Model automatically. Please wait...")
    url = "https://github.com/serengil/deepface_models/releases/download/v1.0/facenet_weights.h5"
    context = ssl._create_unverified_context()

    try:
        with urllib.request.urlopen(url, context=context) as response, open(facenet_path, 'wb') as out_file:
            data = response.read()
            out_file.write(data)
        print("Download complete!")
    except Exception as e:
        print(f"Failed to download model automatically: {e}")
        sys.exit()


def verify_user_face_old(registered_face_path, live_face_path):
    img1 = cv2.imread(registered_face_path)
    img2 = cv2.imread(live_face_path)

    if img1 is None:
        return {"status": False, "message": "Failed to load registered face image."}

    if img2 is None:
        return {"status": False, "message": "Failed to load live face image."}

    try:
        result = DeepFace.verify(img1_path=img1, img2_path=img2, model_name="Facenet", detector_backend="mtcnn",
                                 distance_metric="euclidean_l2")
        if result.get("verified"):
            return {"status": True, "message": "Login Successful. Valid User."}
        else:
            return {"status": False, "message": "Access Denied. Face did not match."}
    except Exception as e:
        return {"status": False, "message": f"Verification Error: {str(e)}"}


def verify_user_face(registered_face_path, live_face_base64):
    try:
        if "," in live_face_base64:
            live_face_base64 = live_face_base64.split(",")[1]

        img_data = base64.b64decode(live_face_base64)
        nparr = np.frombuffer(img_data, np.uint8)
        live_face_img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if live_face_img is None:
            return {"status": False, "message": "Invalid Base64 Image provided."}

        result = DeepFace.verify(
            img1_path=registered_face_path,
            img2_path=live_face_img,
            model_name="Facenet",
            detector_backend="mtcnn",
            distance_metric="euclidean_l2",
            enforce_detection=False,
            threshold=1.17
        )

        if result.get("verified") or (result.get('distance') < 1.17):
            return True
        else:
            return False
    except Exception as e:
        print(e)
        return False
