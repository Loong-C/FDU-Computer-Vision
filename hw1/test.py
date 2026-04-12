import pickle
import numpy as np
import matplotlib.pyplot as plt
from src.dataloader import FashionMNISTDataLoader
from src.model import ThreeLayerMLP

def test():
    loader = FashionMNISTDataLoader(batch_size=128)
    model = ThreeLayerMLP(hidden_dim=256, activation='relu')
    with open('checkpoints/best_model.pkl', 'rb') as f:
        weights = pickle.load(f)
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
    
    visualize_weights(model.layer1.params['W'])

def compute_confusion_matrix(labels, preds, num_classes):
    cm = np.zeros((num_classes, num_classes), dtype=int)
    for l, p in zip(labels, preds):
        cm[l, p] += 1
    return cm

def visualize_weights(W):

    plt.figure(figsize=(8, 8))
    for i in range(16):
        weight_img = W[:, i].reshape(28, 28)
        plt.subplot(4, 4, i + 1)
        plt.imshow(weight_img, cmap='RdBu')
        plt.axis('off')
        plt.title(f"Neuron {i+1}")
    
    plt.suptitle("First Layer Weight Visualization")
    plt.savefig('results/weight_visualization.png')
    plt.show()

if __name__ == "__main__":
    test()