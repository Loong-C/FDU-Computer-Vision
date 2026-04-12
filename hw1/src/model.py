import numpy as np
from src.layers import Linear, ReLU, Sigmoid, Tanh

class MLP:
    def __init__(self, input_dim=784, hidden_dim=256, output_dim=10, activation='relu'):
        self.layer1 = Linear(input_dim, hidden_dim)
        self.layer2 = Linear(hidden_dim, hidden_dim)
        self.layer3 = Linear(hidden_dim, output_dim)
        
        if activation.lower() == 'relu':
            self.act1 = ReLU()
            self.act2 = ReLU()
        elif activation.lower() == 'sigmoid':
            self.act1 = Sigmoid()
            self.act2 = Sigmoid()
        elif activation.lower() == 'tanh':
            self.act1 = Tanh()
            self.act2 = Tanh()
        else:
            raise ValueError("不支持的激活函数类型")

        self.layers = [self.layer1, self.act1, self.layer2, self.act2, self.layer3]

    def forward(self, x):
        for layer in self.layers:
            x = layer.forward(x)
        return x

    def backward(self, grad):
        for layer in reversed(self.layers):
            grad = layer.backward(grad)
        return grad

    def get_params_and_grads(self):
        params = []
        grads = []
        for layer in [self.layer1, self.layer2, self.layer3]:
            params.append(layer.params)
            grads.append(layer.grads)
        return params, grads