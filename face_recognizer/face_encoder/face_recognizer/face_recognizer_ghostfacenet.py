import logging
from pathlib import Path
from typing import List, Tuple, Optional

import cv2
import mediapipe as mp
import numpy as np
import onnxruntime as ort
from skimage.transform import SimilarityTransform

from face_encoder.face_recognizer.face_recognizer import FaceRecognizer

model_path = Path(__file__).resolve().parents[2] / "models/GhostFaceNet.onnx"


LANDMARKS_REF = np.array(
    [
        [38.2946, 51.6963],
        [73.5318, 51.5014],
        [56.0252, 71.7366],
        [41.5493, 92.3655],
        [70.7299, 92.2041],
    ],
    dtype=np.float32,
)

MAX_FACES = 5


class FaceRecognizerGhostFaceNet:
    def __init__(self, model_path: Optional[Path] = None):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info("Initializing FaceRecognizerGhostFaceNet")
        self.model_path = Path(__file__).resolve().parents[2] / "models/GhostFaceNet.onnx"

        self.face_mesh = mp.solutions.face_mesh.FaceMesh(
            static_image_mode=True,
            refine_landmarks=True,
            max_num_faces=MAX_FACES,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        )

        self.session = ort.InferenceSession(str(self.model_path), providers=ort.get_available_providers())
        
        self.similarity_transform = SimilarityTransform()

        input_meta = self.session.get_inputs()[0]
        self.input_name = input_meta.name
        self.logger.info(f"ONNX Model input name: {self.input_name}, shape: {input_meta.shape}")

    def _normalize(self, imgs: List[np.ndarray]) -> np.ndarray:
        arr = np.array(imgs, dtype=np.float32) / 255.0
        return arr

    def _align_face(self, image: np.ndarray, landmarks: np.ndarray) -> np.ndarray:
        self.similarity_transform.estimate(landmarks, LANDMARKS_REF)
        matrix = self.similarity_transform.params[0:2, :]
        aligned = cv2.warpAffine(image, matrix, (112, 112), borderValue=0)
        return aligned

    def _detect_faces_and_landmarks(self, img_rgb: np.ndarray) -> Tuple[List[List[int]], List[np.ndarray]]:
        faces = []
        landmarks_list = []

        results = self.face_mesh.process(img_rgb)
        if not results.multi_face_landmarks:
            self.logger.warning("No faces detected")
            return faces, landmarks_list

        indices = [470, 475, 1, 57, 287]
        h, w, _ = img_rgb.shape

        for face_landmarks in results.multi_face_landmarks:
            points = np.array(
                [(face_landmarks.landmark[i].x * w, face_landmarks.landmark[i].y * h) for i in indices], dtype=np.float32
            )
            landmarks_list.append(points)

            xs = [lm.x * w for lm in face_landmarks.landmark]
            ys = [lm.y * h for lm in face_landmarks.landmark]
            bbox = [int(min(xs)), int(min(ys)), int(max(xs)), int(max(ys))]
            faces.append(bbox)

        return faces, landmarks_list

    def _prepare_aligned_faces(self, img_rgb: np.ndarray, landmarks_list: List[np.ndarray]) -> List[np.ndarray]:
        return [self._align_face(img_rgb, lm) for lm in landmarks_list]

    def _predict_embeddings(self, aligned_faces: List[np.ndarray]) -> List[np.ndarray]:
        if not aligned_faces:
            self.logger.info("No aligned faces to calculate embeddings")
            return []

        normalized = self._normalize(aligned_faces)
        outputs = self.session.run(None, {self.input_name: normalized})
        embeddings = outputs[0]
        return embeddings.tolist()

    def get_image_embeddings(self, image: np.ndarray) -> Tuple[List[np.ndarray], List[List[int]]]:
        bboxes, landmarks = self._detect_faces_and_landmarks(image)
        aligned_faces = self._prepare_aligned_faces(image, landmarks)
        embeddings = self._predict_embeddings(aligned_faces)
        return embeddings, bboxes
