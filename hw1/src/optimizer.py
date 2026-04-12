import numpy as np

class SGDOptimizer:
    def __init__(self, params_list, learning_rate=0.01, weight_decay=0.0, lr_decay=0.95):
        self.params_list = params_list
        self.lr = learning_rate
        self.weight_decay = weight_decay
        self.lr_decay = lr_decay

    def step(self, grads_list):
        for params, grads in zip(self.params_list, grads_list):
            for key in params.keys():
                reg_grad = self.weight_decay * params[key] if key == 'W' else 0
                params[key] -= self.lr * (grads[key] + reg_grad)

    def decay_learning_rate(self):
        self.lr *= self.lr_decay