import os
import gzip
import numpy as np
import urllib.request

class FashionMNISTDataLoader:
    def __init__(self, data_dir='data', batch_size=64, val_split=0.1, shuffle=True):
        self.data_dir = data_dir
        self.batch_size = batch_size
        self.val_split = val_split
        self.shuffle = shuffle
        
        self.base_url = 'http://fashion-mnist.s3-website.eu-central-1.amazonaws.com/'
        self.files = {
            'train_img': 'train-images-idx3-ubyte.gz',
            'train_label': 'train-labels-idx1-ubyte.gz',
            'test_img': 't10k-images-idx3-ubyte.gz',
            'test_label': 't10k-labels-idx1-ubyte.gz'
        }
        
        self._prepare_data()

    def _prepare_data(self):
        """下载并加载数据"""
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
        if all(os.path.exists(os.path.join(self.data_dir, file)) for file in self.files.values()):
            pass
        else:
            for file in self.files.values():
                path = os.path.join(self.data_dir, file)
                if not os.path.exists(path):
                    print(f"正在下载 {file}...")
                    urllib.request.urlretrieve(self.base_url + file, path)

        train_images = self._load_images(os.path.join(self.data_dir, self.files['train_img']))
        train_labels = self._load_labels(os.path.join(self.data_dir, self.files['train_label']))
        test_images = self._load_images(os.path.join(self.data_dir, self.files['test_img']))
        test_labels = self._load_labels(os.path.join(self.data_dir, self.files['test_label']))

        # 预处理
        train_images = train_images.astype(np.float32) / 255.0
        test_images = test_images.astype(np.float32) / 255.0

        # 划分训练集和验证集 
        num_train = int(len(train_images) * (1 - self.val_split))
        indices = np.arange(len(train_images))
        if self.shuffle:
            np.random.shuffle(indices)
            
        self.train_data = (train_images[indices[:num_train]], train_labels[indices[:num_train]])
        self.val_data = (train_images[indices[num_train:]], train_labels[indices[num_train:]])
        self.test_data = (test_images, test_labels)

    def _load_images(self, path):
        with gzip.open(path, 'rb') as f:
            data = np.frombuffer(f.read(), np.uint8, offset=16)
        return data.reshape(-1, 784) # 展平为 28x28 = 784 维向量

    def _load_labels(self, path):
        with gzip.open(path, 'rb') as f:
            return np.frombuffer(f.read(), np.uint8, offset=8)

    def get_batches(self, set_name='train'):
        if set_name == 'train':
            images, labels = self.train_data
        elif set_name == 'val':
            images, labels = self.val_data
        else:
            images, labels = self.test_data
            
        num_samples = len(images)
        indices = np.arange(num_samples)
        if self.shuffle and set_name == 'train':
            np.random.shuffle(indices)
            
        for i in range(0, num_samples, self.batch_size):
            batch_idx = indices[i:i + self.batch_size]
            yield images[batch_idx], labels[batch_idx]

if __name__ == "__main__":
    '''测试'''
    import matplotlib.pyplot as plt
    loader = FashionMNISTDataLoader(batch_size=4)
    images, labels = next(loader.get_batches('train'))
    print(f"Batch images shape: {images.shape}")
    print(f"Batch labels: {labels}")
    plt.imshow(images[0].reshape(28, 28), cmap='gray')
    plt.title(f"Label: {labels[0]}")
    plt.show()
