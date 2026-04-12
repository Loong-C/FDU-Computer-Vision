# src/train.py 修改后的核心部分
import os
import pickle
import numpy as np
import matplotlib.pyplot as plt
from src.dataloader import FashionMNISTDataLoader
from src.model import MLP
from src.loss import SoftmaxCrossEntropy
from src.optimizer import SGDOptimizer

DEFAULT_CONFIG = {
    'hidden_dim': 1024,
    'activation': 'relu',
    'lr': 0.01,
    'weight_decay': 1e-4,
    'lr_decay': 0.95,
    'epochs': 500,
    'batch_size': 512,
}

def train_model(config, save=True, save_path='checkpoints/best_model.pkl'):
    """
    config: 包含 lr, hidden_dim, weight_decay, epochs 等的字典
    """
    loader = FashionMNISTDataLoader(batch_size=config['batch_size'])
    model = MLP(hidden_dim=config['hidden_dim'], activation=config['activation'])
    criterion = SoftmaxCrossEntropy()
    
    params, grads = model.get_params_and_grads()
    optimizer = SGDOptimizer(params, learning_rate=config['lr'], 
                             weight_decay=config['weight_decay'], 
                             lr_decay=config['lr_decay'])

    history = {'train_loss': [], 'val_loss': [], 'val_acc': []}
    best_val_acc = 0.0

    for epoch in range(config['epochs']):
        epoch_losses = []
        for images, labels in loader.get_batches('train'):
            output = model.forward(images)
            loss = criterion.forward(output, labels)
            grad_output = criterion.backward()
            model.backward(grad_output)
            optimizer.step(grads)
            epoch_losses.append(loss)
        
        avg_train_loss = np.mean(epoch_losses)
        optimizer.decay_learning_rate()

        # 验证
        val_loss_list = []
        correct = 0
        total = 0
        for images, labels in loader.get_batches('val'):
            output = model.forward(images)
            val_loss_list.append(criterion.forward(output, labels))
            
            preds = np.argmax(output, axis=1)
            correct += np.sum(preds == labels)
            total += labels.shape[0]
        
        avg_val_loss = np.mean(val_loss_list)
        val_acc = correct / total

        history['train_loss'].append(avg_train_loss)
        history['val_loss'].append(avg_val_loss)
        history['val_acc'].append(val_acc)
        if (epoch + 1) % 10 == 0 or epoch == config['epochs'] - 1:
            print(f"Epoch [{epoch+1}/{config['epochs']}] - Loss: {avg_train_loss:.4f}, Val Acc: {val_acc:.4f}, LR: {optimizer.lr:.6f}")
        
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            if save == True:
                os.makedirs(os.path.dirname(save_path), exist_ok=True)
                with open(save_path, 'wb') as f:
                    pickle.dump(model.get_params_and_grads()[0], f)   
    return best_val_acc, history


    

def plot_history(history):
    plt.figure(figsize=(12, 4))
    plt.subplot(1, 2, 1)
    plt.plot(history['train_loss'], label='Train Loss')
    plt.plot(history['val_loss'], label='Val Loss')
    plt.title('Loss Curve')
    plt.legend()
    
    plt.subplot(1, 2, 2)
    plt.plot(history['val_acc'], label='Val Accuracy')
    plt.title('Validation Accuracy')
    plt.legend()
    
    if not os.path.exists('results'): os.makedirs('results')
    plt.savefig('results/training_curves.png')
    plt.show()

if __name__ == "__main__":
    best_val_acc, history = train_model(DEFAULT_CONFIG, save=True, save_path='checkpoints/best_model.pkl')
    print(f"Best validation accuracy: {best_val_acc:.4f}")
    plot_history(history)
