import os
import pickle
import numpy as np
import matplotlib.pyplot as plt
from src.dataloader import FashionMNISTDataLoader
from src.model import MLP

CLASS_NAMES = ['T-shirt/top', 'Trouser', 'Pullover', 'Dress', 'Coat',
               'Sandal', 'Shirt', 'Sneaker', 'Bag', 'Ankle boot']

def test(model_path='checkpoints/best_model.pkl', batch_size=512):
    loader = FashionMNISTDataLoader(batch_size=batch_size, shuffle=False)
    with open(model_path, 'rb') as f:
        weights = pickle.load(f)
    hidden_dim = weights[0]['W'].shape[1]
    model = MLP(hidden_dim=hidden_dim, activation='relu')
    model.layer1.params = weights[0]
    model.layer2.params = weights[1]
    model.layer3.params = weights[2]

    all_preds = []
    all_labels = []
    
    for images, labels in loader.get_batches('test'):
        output = model.forward(images)
        preds = np.argmax(output, axis=1)
        all_preds.extend(preds)
        all_labels.extend(labels)
    
    all_preds = np.array(all_preds)
    all_labels = np.array(all_labels)
    
    accuracy = np.mean(all_preds == all_labels)
    print(f"测试集准确率 (Test Accuracy): {accuracy * 100:.2f}%")

    cm = compute_confusion_matrix(all_labels, all_preds, num_classes=10)
    print("\n混淆矩阵 (Confusion Matrix):")
    print(cm)
    plot_confusion_matrix(cm)
    save_test_metrics(accuracy, cm)
    return accuracy, cm

def compute_confusion_matrix(labels, preds, num_classes):
    cm = np.zeros((num_classes, num_classes), dtype=int)
    for l, p in zip(labels, preds):
        cm[l, p] += 1
    return cm

def plot_confusion_matrix(cm, save_path='results/confusion_matrix.png'):
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    plt.figure(figsize=(8.5, 7))
    plt.imshow(cm, cmap='Blues')
    plt.title('Confusion Matrix on Test Set')
    plt.xlabel('Predicted Label')
    plt.ylabel('True Label')
    plt.xticks(range(len(CLASS_NAMES)), CLASS_NAMES, rotation=45, ha='right')
    plt.yticks(range(len(CLASS_NAMES)), CLASS_NAMES)
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            color = 'white' if cm[i, j] > cm.max() * 0.55 else 'black'
            plt.text(j, i, str(cm[i, j]), ha='center', va='center', fontsize=7, color=color)
    plt.tight_layout()
    plt.savefig(save_path, dpi=200)
    plt.close()

def save_test_metrics(accuracy, cm, save_path='results/test_metrics.txt'):
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    with open(save_path, 'w', encoding='utf-8') as f:
        f.write(f"Test Accuracy: {accuracy:.4f}\n")
        f.write("Confusion Matrix:\n")
        for row in cm:
            f.write(" ".join(map(str, row)) + "\n")

if __name__ == "__main__":
    test()
