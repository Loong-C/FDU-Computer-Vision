import numpy as np

class Linear:
    def __init__(self, input_dim, output_dim):
        self.params = {
            'W': np.random.randn(input_dim, output_dim) * np.sqrt(2. / input_dim),
            'b': np.zeros((1, output_dim))
        }
        self.grads = {
            'W': np.zeros_like(self.params['W']),
            'b': np.zeros_like(self.params['b'])
        }
        self.x = None

    def forward(self, x):
        self.x = x
        return np.dot(x, self.params['W']) + self.params['b']

    def backward(self, grad_output):
        # dL/dW = X^T * dL/dY
        self.grads['W'] = np.dot(self.x.T, grad_output)
        # dL/db = sum(dL/dY)
        self.grads['b'] = np.sum(grad_output, axis=0, keepdims=True)
        
        # dL/dX = dL/dY * W^T
        grad_input = np.dot(grad_output, self.params['W'].T)
        return grad_input

class ReLU:
    def __init__(self):
        self.mask = None

    def forward(self, x):
        self.mask = (x <= 0)
        out = x.copy()
        out[self.mask] = 0
        return out

    def backward(self, grad_output):
        grad_input = grad_output.copy()
        grad_input[self.mask] = 0
        return grad_input

class Sigmoid:
    def __init__(self):
        self.out = None

    def forward(self, x):
        # f(x) = 1 / (1 + exp(-x)) 
        self.out = 1 / (1 + np.exp(-np.clip(x, -500, 500))) # clip 防止溢出
        return self.out

    def backward(self, grad_output):
        # f'(x) = f(x) * (1 - f(x))
        grad_input = grad_output * (self.out * (1 - self.out))
        return grad_input

class Tanh:
    def __init__(self):
        self.out = None

    def forward(self, x):
        self.out = np.tanh(x)
        return self.out

    def backward(self, grad_output):
        # f'(x) = 1 - tanh^2(x)
        grad_input = grad_output * (1 - self.out**2)
        return grad_input