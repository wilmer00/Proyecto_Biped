#!/usr/bin/env python3
"""
Script para entrenar el modelo de detección de minerales
"""
import sys
import os

# Añadir directorio padre al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai.mineral_detector import MineralDetector
from config.settings import Config


def main():
    print("="*60)
    print("ENTRENAMIENTO DEL MODELO DE DETECCIÓN DE MINERALES")
    print("="*60)
    print()
    
    # Verificar dataset
    if not os.path.exists(Config.DATASET_PATH):
        print(f"❌ Error: No se encuentra la carpeta {Config.DATASET_PATH}")
        print("\nEstructura requerida:")
        print("datasets/")
        print("  ├── mineral1/")
        print("  │   ├── img1.jpg")
        print("  │   ├── img2.jpg")
        print("  ├── mineral2/")
        print("  │   ├── img1.jpg")
        print("  └── ...")
        return
    
    # Contar clases e imágenes
    classes = [d for d in os.listdir(Config.DATASET_PATH) 
               if os.path.isdir(os.path.join(Config.DATASET_PATH, d))]
    
    if len(classes) == 0:
        print("❌ Error: No se encontraron clases en el dataset")
        print(f"Crea carpetas con imágenes en: {Config.DATASET_PATH}")
        return
    
    print(f"📁 Dataset encontrado:")
    print(f"   Ruta: {Config.DATASET_PATH}")
    print(f"   Clases: {len(classes)}")
    
    total_images = 0
    for class_name in classes:
        class_path = os.path.join(Config.DATASET_PATH, class_name)
        images = [f for f in os.listdir(class_path) 
                 if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        print(f"   - {class_name}: {len(images)} imágenes")
        total_images += len(images)
    
    print(f"\n📊 Total de imágenes: {total_images}")
    
    if total_images < 20:
        print("\n⚠️ ADVERTENCIA: Pocas imágenes para entrenar")
        print("   Se recomienda al menos 20 imágenes por clase")
    
    # Confirmar entrenamiento
    print("\n" + "="*60)
    response = input("¿Desea iniciar el entrenamiento? (s/n): ")
    
    if response.lower() != 's':
        print("Entrenamiento cancelado")
        return
    
    # Parámetros de entrenamiento
    print("\n⚙️ Configuración:")
    epochs_input = input(f"Épocas (default: 20): ")
    epochs = int(epochs_input) if epochs_input.strip() else 20
    
    batch_input = input(f"Batch size (default: 32): ")
    batch_size = int(batch_input) if batch_input.strip() else 32
    
    print(f"\n🏋️ Iniciando entrenamiento...")
    print(f"   Épocas: {epochs}")
    print(f"   Batch size: {batch_size}")
    print()
    
    # Crear detector y entrenar
    detector = MineralDetector()
    
    success = detector.train(
        dataset_path=Config.DATASET_PATH,
        epochs=epochs,
        batch_size=batch_size
    )
    
    if success:
        print("\n" + "="*60)
        print("✅ ENTRENAMIENTO COMPLETADO")
        print("="*60)
        print(f"Modelo guardado en: {Config.MODEL_PATH}")
        print("\nPuedes usar el modelo ejecutando:")
        print("  python main.py")
        print()
    else:
        print("\n❌ Error en el entrenamiento")


if __name__ == "__main__":
    main()