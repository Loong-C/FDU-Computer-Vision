import torch
from torch.utils.data import DataLoader, random_split
from torchvision import datasets, transforms


def build_transforms(image_size: int = 224):
    train_transform = transforms.Compose([
        transforms.Resize((image_size, image_size)),
        transforms.RandomHorizontalFlip(p=0.5),
        transforms.RandomRotation(degrees=15),
        transforms.ColorJitter(
            brightness=0.2,
            contrast=0.2,
            saturation=0.2
        ),
        transforms.ToTensor(),
        transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225]
        )
    ])

    eval_transform = transforms.Compose([
        transforms.Resize((image_size, image_size)),
        transforms.ToTensor(),
        transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225]
        )
    ])

    return train_transform, eval_transform


def build_dataloaders(
    root: str = "./data",
    image_size: int = 224,
    batch_size: int = 32,
    num_workers: int = 4,
    val_ratio: float = 0.2,
    seed: int = 42
):
    train_transform, eval_transform = build_transforms(image_size)

    full_trainval_for_split = datasets.OxfordIIITPet(
        root=root,
        split="trainval",
        target_types="category",
        transform=train_transform,
        download=True
    )

    full_trainval_for_eval = datasets.OxfordIIITPet(
        root=root,
        split="trainval",
        target_types="category",
        transform=eval_transform,
        download=True
    )

    test_dataset = datasets.OxfordIIITPet(
        root=root,
        split="test",
        target_types="category",
        transform=eval_transform,
        download=True
    )

    total_size = len(full_trainval_for_split)
    val_size = int(total_size * val_ratio)
    train_size = total_size - val_size

    generator = torch.Generator().manual_seed(seed)

    train_subset, val_subset_indices = random_split(
        range(total_size),
        [train_size, val_size],
        generator=generator
    )

    train_indices = list(train_subset)
    val_indices = list(val_subset_indices)

    train_dataset = torch.utils.data.Subset(
        full_trainval_for_split,
        train_indices
    )

    val_dataset = torch.utils.data.Subset(
        full_trainval_for_eval,
        val_indices
    )

    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=num_workers,
        pin_memory=True
    )

    val_loader = DataLoader(
        val_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=True
    )

    test_loader = DataLoader(
        test_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=True
    )

    class_names = full_trainval_for_split.classes

    return train_loader, val_loader, test_loader, class_names


if __name__ == "__main__":
    train_loader, val_loader, test_loader, class_names = build_dataloaders(
        root="./data",
        image_size=224,
        batch_size=8,
        num_workers=0,
        val_ratio=0.2,
        seed=42
    )

    images, labels = next(iter(train_loader))

    print("Number of classes:", len(class_names))
    print("Class names:", class_names[:5], "...")
    print("Train batches:", len(train_loader))
    print("Val batches:", len(val_loader))
    print("Test batches:", len(test_loader))
    print("Image batch shape:", images.shape)
    print("Label batch shape:", labels.shape)
    print("Label examples:", labels[:8])