# ============================================
# SISTEMA DE LOCALIZACIÓN (GRAD-CAM + BOUNDING BOX)
# ============================================
import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers, models, callbacks
import cv2
import json

class MineralLocalizer:
  """
  Clase para detectar y localizar minerales en imágenes.
  Uso posterior al entrenamiento.
  """
  
  def __init__(self, model_path, classes_path, img_size=(224, 224)):
      """
      Inicializa el localizador
      
      Args:
          model_path: Ruta al modelo .h5
          classes_path: Ruta al archivo JSON con clases
          img_size: Tamaño de imagen para procesamiento
      """
      self.model = models.load_model(model_path)
      with open(classes_path, 'r') as f:
          self.classes = json.load(f)
      
      self.img_size = img_size
      self.last_conv_layer_name = self._find_last_conv_layer()
      
      print(f"✓ Localizador cargado:")
      print(f"  - Modelo: {model_path}")
      print(f"  - Clases: {len(self.classes)}")
      print(f"  - Última capa conv: {self.last_conv_layer_name}")
  
  def _find_last_conv_layer(self):
      """Encuentra automáticamente la última capa convolucional"""
      for layer in reversed(self.model.layers):
          if isinstance(layer, layers.Conv2D):
              return layer.name
      return "top_conv"  # Fallback para EfficientNet
  
  def preprocess_image(self, image_path):
      """Carga y preprocesa una imagen"""
      img = keras.preprocessing.image.load_img(
          image_path, target_size=self.img_size
      )
      img_array = keras.preprocessing.image.img_to_array(img)
      img_array = np.expand_dims(img_array, axis=0)
      img_array = tf.keras.applications.efficientnet.preprocess_input(img_array)
      return img_array, img
  
  def generate_gradcam(self, img_array, class_index):
      """Genera heatmap Grad-CAM"""
      grad_model = models.Model(
          inputs=self.model.inputs,
          outputs=[
              self.model.get_layer(self.last_conv_layer_name).output,
              self.model.output
          ]
      )
      
      with tf.GradientTape() as tape:
          conv_outputs, predictions = grad_model(img_array)
          loss = predictions[:, class_index]
      
      grads = tape.gradient(loss, conv_outputs)
      pooled_grads = tf.reduce_mean(grads, axis=(0, 1, 2))
      
      conv_outputs = conv_outputs[0]
      heatmap = tf.reduce_mean(
          tf.multiply(pooled_grads, conv_outputs), axis=-1
      )
      heatmap = np.maximum(heatmap, 0)
      heatmap /= np.max(heatmap) if np.max(heatmap) > 0 else 1
      
      return heatmap
  
  def get_bounding_box(self, heatmap, threshold=0.5):
      """Extrae bounding box desde heatmap"""
      if np.max(heatmap) == 0:
          return None
      
      # Redimensionar heatmap
      heatmap_resized = cv2.resize(heatmap.numpy(), self.img_size)
      heatmap_resized = np.uint8(255 * heatmap_resized)
      
      # Umbralización
      _, thresh = cv2.threshold(
          heatmap_resized, int(255 * threshold), 255, cv2.THRESH_BINARY
      )
      
      # Encontrar contornos
      contours, _ = cv2.findContours(
          thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
      )
      
      if not contours:
          return None
      
      # Encontrar el contorno más grande
      max_contour = max(contours, key=cv2.contourArea)
      
      # Filtrar por área mínima
      if cv2.contourArea(max_contour) < 100:  # Ajustar según necesidad
          return None
      
      x, y, w, h = cv2.boundingRect(max_contour)
      
      return (x, y, x + w, y + h)
  
  def predict_single(self, image_path):
      """
      Predice y localiza mineral en una imagen
      
      Returns:
          dict con 'class', 'confidence', 'bbox', 'heatmap'
      """
      # Preprocesar
      img_array, original_img = self.preprocess_image(image_path)
      
      # Predicción
      predictions = self.model.predict(img_array, verbose=0)[0]
      class_index = np.argmax(predictions)
      confidence = predictions[class_index]
      
      # Generar heatmap y bbox solo si confianza es alta
      if confidence > 0.5:
          heatmap = self.generate_gradcam(img_array, class_index)
          bbox = self.get_bounding_box(heatmap, threshold=0.5)
      else:
          heatmap = np.zeros((7, 7))  # Tamaño mínimo
          bbox = None
      
      return {
          "class": self.classes[class_index],
          "confidence": float(confidence),
          "bbox": bbox,
          "heatmap": heatmap,
          "all_predictions": predictions,
          "original_image": original_img
      }