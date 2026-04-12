import numpy as np

class SoftmaxCrossEntropy:
    def __init__(self):
        self.softmax_output = None
        self.labels = None

    def forward(self, x, labels):

        exps = np.exp(x - np.max(x, axis=1, keepdims=True))
        self.softmax_output = exps / np.sum(exps, axis=1, keepdims=True)
        self.labels = labels
        batch_size = x.shape[0]
        correct_logprobs = -np.log(self.softmax_output[range(batch_size), labels] + 1e-12)
        loss = np.sum(correct_logprobs) / batch_size
        return loss

    def backward(self):
        batch_size = self.labels.shape[0]
        grad = self.softmax_output.copy()
        grad[range(batch_size), self.labels] -= 1
        return grad / batch_size