
import numpy as np
import pickle
from train import train_model
from search_param import grid_search
from src.dataloader import FashionMNISTDataLoader
from src.model import MLP
from src.utils import plot_curves, visualize_first_layer_weights, error_analysis

def run_pipeline():
    print("超参数搜索：")
    best_config = grid_search()

    print("\n训练:")
    best_config['epochs'] = 500
    _, history = train_model(best_config, save=True, save_path='checkpoints/best_model.pkl')
    plot_curves(history)

    print("\n测试集与可视化")
    loader = FashionMNISTDataLoader()
    model = MLP(hidden_dim=best_config['hidden_dim'])
    
    # 加载最优权重
    with open('checkpoints/best_model.pkl', 'rb') as f:
        best_weights = pickle.load(f)
    model.layer1.params = best_weights[0]
    model.layer2.params = best_weights[1]
    model.layer3.params = best_weights[2]

    # 运行可视化和错例分析
    visualize_first_layer_weights(model.layer1.params['W']) 
    error_analysis(model, loader)
    print("所有结果已保存")

if __name__ == "__main__":
    run_pipeline()