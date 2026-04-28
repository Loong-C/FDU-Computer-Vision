import random
from typing import Tuple

import torch
from torch.utils.data import Dataset, DataLoader, random_split
from torchvision.datasets import OxfordIIITPet
from torchvision.transforms import functional as F
from torchvision.transforms import InterpolationMode


class OxfordPetSegmentation(Dataset):
    """
    Oxford-IIIT Pet semantic segmentation dataset.

    The original trimap mask has pixel values:
        1: pet
        2: background
        3: border

    We convert them to:
        0: pet
        1: background
        2: border

    The returned image shape is [3, H, W].
    The returned mask shape is [H, W].
    """

    def __init__(
        self,
        root: str,
        split: str = "trainval",
        image_size: int = 256,
        download: bool = True,
        augment: bool = False,
    ):
        self.dataset = OxfordIIITPet(
            root=root,
            split=split,
            target_types="segmentation",
            download=download,
        )

        self.image_size = image_size
        self.augment = augment

    def __len__(self):
        return len(self.dataset)

    def _transform(self, image, mask):
        image = F.resize(
            image,
            size=[self.image_size, self.image_size],
            interpolation=InterpolationMode.BILINEAR,
        )

        mask = F.resize(
            mask,
            size=[self.image_size, self.image_size],
            interpolation=InterpolationMode.NEAREST,
        )

        if self.augment:
            if random.random() < 0.5:
                image = F.hflip(image)
                mask = F.hflip(mask)

        image = F.to_tensor(image)

        image = F.normalize(
            image,
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225],
        )

        mask = torch.as_tensor(
            data=list(mask.getdata()),
            dtype=torch.long,
        ).view(self.image_size, self.image_size)

        mask = mask - 1

        return image, mask

    def __getitem__(self, index):
        image, mask = self.dataset[index]
        image, mask = self._transform(image, mask)

        return image, mask


def build_dataloaders(config: dict) -> Tuple[DataLoader, DataLoader]:
    data_config = config["data"]

    base_dataset = OxfordPetSegmentation(
        root=data_config["root"],
        split="trainval",
        image_size=data_config["image_size"],
        download=True,
        augment=False,
    )

    dataset_size = len(base_dataset)
    val_ratio = data_config["val_ratio"]
    val_size = int(dataset_size * val_ratio)
    train_size = dataset_size - val_size

    generator = torch.Generator().manual_seed(config["seed"])

    train_subset, val_subset = random_split(
        range(dataset_size),
        lengths=[train_size, val_size],
        generator=generator,
    )

    train_dataset = OxfordPetSegmentation(
        root=data_config["root"],
        split="trainval",
        image_size=data_config["image_size"],
        download=False,
        augment=True,
    )

    val_dataset = OxfordPetSegmentation(
        root=data_config["root"],
        split="trainval",
        image_size=data_config["image_size"],
        download=False,
        augment=False,
    )

    train_dataset = torch.utils.data.Subset(train_dataset, train_subset.indices)
    val_dataset = torch.utils.data.Subset(val_dataset, val_subset.indices)

    train_loader = DataLoader(
        train_dataset,
        batch_size=data_config["batch_size"],
        shuffle=True,
        num_workers=data_config["num_workers"],
        pin_memory=True,
    )

    val_loader = DataLoader(
        val_dataset,
        batch_size=data_config["batch_size"],
        shuffle=False,
        num_workers=data_config["num_workers"],
        pin_memory=True,
    )

    return train_loader, val_loader