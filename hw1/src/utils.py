# src/utils.py
import numpy as np
import matplotlib.pyplot as plt

def plot_curves(history, save_path='results/curves.png'):
    """可视化 Loss 和 Accuracy 曲线"""
    plt.figure(figsize=(12, 4))
    plt.subplot(1, 2, 1)
    plt.plot(history['train_loss'], label='Train')
    plt.plot(history['val_loss'], label='Val')
    plt.title('Loss')
    plt.subplot(1, 2, 2)
    plt.plot(history['val_acc'], label='Val Acc')
    plt.title('Accuracy')
    plt.savefig(save_path)
    plt.close()

def visualize_first_layer_weights(weights, save_path='results/weights.png'):
    """可视化第一层权重 """

    plt.figure(figsize=(10, 10))
    for i in range(16):
        plt.subplot(4, 4, i+1)
        grid = weights[:, i].reshape(28, 28)
        plt.imshow(grid, cmap='viridis')
        plt.axis('off')
    plt.savefig(save_path)
    plt.close()

def error_analysis(model, loader, num_samples=5, save_path='results/errors.png'):
    """错例分析 """
    images_list, labels_list, preds_list = [], [], []
    for imgs, lbls in loader.get_batches('test'):
        outputs = model.forward(imgs)
        preds = np.argmax(outputs, axis=1)
        error_mask = (preds != lbls)
        if np.any(error_mask):
            images_list.extend(imgs[error_mask])
            labels_list.extend(lbls[error_mask])
            preds_list.extend(preds[error_mask])
        
        if len(images_list) >= num_samples: break

    plt.figure(figsize=(15, 3))
    classes = ['T-shirt', 'Trouser', 'Pullover', 'Dress', 'Coat', 'Sandal', 'Shirt', 'Sneaker', 'Bag', 'Ankle boot']
    for i in range(num_samples):
        plt.subplot(1, num_samples, i+1)
        plt.imshow(images_list[i].reshape(28, 28), cmap='gray')
        plt.title(f"True:{classes[labels_list[i]]}\nPred:{classes[preds_list[i]]}")
        plt.axis('off')
    plt.savefig(save_path)
    plt.close()