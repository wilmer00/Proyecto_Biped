"""
Detector de minerales usando CNN
"""
import cv2
import numpy as np
import os
from keras.models import Sequential, load_model
from keras.layers import Conv2D, MaxPooling2D, Flatten, Dense, Dropout
from tensorflow.keras.preprocessing.image import ImageDataGenerator

from config.settings import Config


class MineralDetector:
    """Detector de minerales basado en visión artificial"""
    
    def __init__(self):
        self.model = None
        self.class_names = []
        self.is_trained = False
        
    def build_model(self, num_classes):
        """Construir arquitectura de la CNN"""
        model = Sequential([
            Conv2D(32, (3, 3), activation='relu', 
                   input_shape=(*Config.IMAGE_SIZE, 3)),
            MaxPooling2D(2, 2),
            
            Conv2D(64, (3, 3), activation='relu'),
            MaxPooling2D(2, 2),
            
            Conv2D(128, (3, 3), activation='relu'),
            MaxPooling2D(2, 2),
            
            Flatten(),
            Dense(512, activation='relu'),
            Dropout(0.5),
            Dense(num_classes, activation='softmax')
        ])
        
        model.compile(
            optimizer='adam',
            loss='categorical_crossentropy',
            metrics=['accuracy']
        )
        
        return model
    
    def train(self, dataset_path=None, epochs=20, batch_size=32):
        """
        Entrenar el modelo con las imágenes en datasets/
        
        Estructura esperada:
        datasets/
            ├── mineral1/
            │   ├── img1.jpg
            │   ├── img2.jpg
            ├── mineral2/
            │   ├── img1.jpg
        """
        dataset_path = dataset_path or Config.DATASET_PATH
        
        if not os.path.exists(dataset_path):
            print(f"❌ Dataset no encontrado: {dataset_path}")
            return False
        
        # Obtener clases (carpetas en datasets/)
        self.class_names = [d for d in os.listdir(dataset_path) 
                           if os.path.isdir(os.path.join(dataset_path, d))]
        
        if len(self.class_names) == 0:
            print("❌ No se encontraron clases de minerales")
            return False
        
        print(f"🎯 Clases detectadas: {self.class_names}")
        
        # Data augmentation
        datagen = ImageDataGenerator(
            rescale=1./255,
            rotation_range=20,
            width_shift_range=0.2,
            height_shift_range=0.2,
            horizontal_flip=True,
            validation_split=0.2
        )
        
        # Generadores de entrenamiento y validación
        train_generator = datagen.flow_from_directory(
            dataset_path,
            target_size=Config.IMAGE_SIZE,
            batch_size=batch_size,
            class_mode='categorical',
            subset='training'
        )
        
        validation_generator = datagen.flow_from_directory(
            dataset_path,
            target_size=Config.IMAGE_SIZE,
            batch_size=batch_size,
            class_mode='categorical',
            subset='validation'
        )
        
        # Construir modelo
        num_classes = len(self.class_names)
        self.model = self.build_model(num_classes)
        
        print(f"🏋️ Entrenando modelo con {num_classes} clases...")
        
        # Entrenar
        history = self.model.fit(
            train_generator,
            epochs=epochs,
            validation_data=validation_generator,
            verbose=1
        )
        
        # Guardar modelo
        os.makedirs("models", exist_ok=True)
        self.model.save(Config.MODEL_PATH)
        print(f"✅ Modelo guardado en: {Config.MODEL_PATH}")
        
        self.is_trained = True
        return True
    
    def load_model(self, model_path=None):
        """Cargar modelo previamente entrenado"""
        model_path = model_path or Config.MODEL_PATH
        
        if not os.path.exists(model_path):
            print(f"❌ Modelo no encontrado: {model_path}")
            return False
        
        try:
            self.model = load_model(model_path)
            
            # Cargar nombres de clases desde dataset
            dataset_path = Config.DATASET_PATH
            if os.path.exists(dataset_path):
                self.class_names = [d for d in os.listdir(dataset_path) 
                                   if os.path.isdir(os.path.join(dataset_path, d))]
            
            self.is_trained = True
            print(f"✅ Modelo cargado: {len(self.class_names)} clases")
            return True
            
        except Exception as e:
            print(f"❌ Error cargando modelo: {e}")
            return False
    
    def predict(self, frame):
        """
        Detectar minerales en un frame
        
        Args:
            frame: imagen BGR de OpenCV
            
        Returns:
            dict con {
                'detected': bool,
                'class': str,
                'confidence': float,
                'bbox': (x, y, w, h) o None
            }
        """
        if not self.is_trained or self.model is None:
            return {
                'detected': False,
                'class': None,
                'confidence': 0.0,
                'bbox': None
            }
        
        # Preprocesar imagen
        img = cv2.resize(frame, Config.IMAGE_SIZE)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img = img.astype('float32') / 255.0
        img = np.expand_dims(img, axis=0)
        
        # Predicción
        predictions = self.model.predict(img, verbose=0)[0]
        class_idx = np.argmax(predictions)
        confidence = float(predictions[class_idx])
        
        # Verificar umbral de confianza
        if confidence < Config.CONFIDENCE_THRESHOLD:
            return {
                'detected': False,
                'class': None,
                'confidence': confidence,
                'bbox': None
            }
        
        detected_class = self.class_names[class_idx] if class_idx < len(self.class_names) else "Unknown"
        
        # Detectar región (simplificado - detección de blob de color)
        bbox = self._find_mineral_region(frame)
        
        return {
            'detected': True,
            'class': detected_class,
            'confidence': confidence,
            'bbox': bbox
        }
    
    def _find_mineral_region(self, frame):
        """
        Encontrar región del mineral en la imagen
        Usa detección de color/contraste simplificada
        """
        try:
            # Convertir a HSV para mejor segmentación
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            
            # Umbral adaptativo
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # Encontrar contornos
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            if contours:
                # Obtener el contorno más grande
                largest = max(contours, key=cv2.contourArea)
                x, y, w, h = cv2.boundingRect(largest)
                
                # Filtrar contornos muy pequeños
                if w * h > 1000:
                    return (x, y, w, h)
            
        except Exception as e:
            print(f"Error en detección de región: {e}")
        
        return None
    
    def draw_detection(self, frame, detection):
        """
        Dibujar resultado de detección en el frame
        
        Args:
            frame: imagen OpenCV
            detection: resultado de predict()
            
        Returns:
            frame con anotaciones
        """
        annotated = frame.copy()
        
        if detection['detected']:
            # Dibujar bounding box si existe
            if detection['bbox']:
                x, y, w, h = detection['bbox']
                cv2.rectangle(annotated, (x, y), (x+w, y+h), (0, 255, 0), 2)
            
            # Texto con clase y confianza
            text = f"{detection['class']}: {detection['confidence']:.2%}"
            cv2.putText(annotated, text, (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            
            # Indicador visual
            cv2.putText(annotated, "MINERAL DETECTADO", (10, 60),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        else:
            cv2.putText(annotated, "Buscando minerales...", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
        
        return annotated