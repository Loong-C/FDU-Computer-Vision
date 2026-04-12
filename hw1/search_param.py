import numpy as np
from train import train_model

def grid_search():

    lrs = [1e-2, 1e-2, 1e-3, 1e-4]
    hidden_dims = [128, 256, 512, 1024]
    reg_strengths = [1e-3, 1e-4, 1e-5]
    
    results = []
    best_config = None
    best_acc = -1
    for lr in lrs:
        for hd in hidden_dims:
            for wd in reg_strengths:
                print(f"\n测试组合: lr={lr}, hidden={hd}, weight_decay={wd}")
                config = {
                    'hidden_dim': hd, 'activation': 'relu',
                    'lr': lr, 'weight_decay': wd,
                    'lr_decay': 0.95, 'epochs': 30, 'batch_size': 512
                }
                acc = train_model(config, save=False)[0]
                results.append((lr, hd, wd, acc))
                if acc > best_acc:
                    best_acc = acc
                    best_config = config

    print("\n--- 超参数搜索结果汇总 ---")
    print("LR | Hidden | WeightDecay | Best Val Acc")
    for res in results:
        print(f"{res[0]} | {res[1]} | {res[2]} | {res[3]:.4f}")
    print(f"\n最佳配置: {best_config}, Val Acc: {best_acc:.4f}")
    return best_config

if __name__ == "__main__":
    grid_search()