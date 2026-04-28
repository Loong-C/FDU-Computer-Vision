import torch

from datasets.oxford_pet import build_dataloaders
from losses.dice_loss import build_loss
from main import load_config
from models.unet import UNet


def test_loss(config_path: str):
    config = load_config(config_path)

    train_loader, _ = build_dataloaders(config)
    images, masks = next(iter(train_loader))

    model = UNet(
        in_channels=config["model"]["in_channels"],
        num_classes=config["model"]["num_classes"],
        base_channels=config["model"]["base_channels"],
    )

    criterion = build_loss(config)

    with torch.no_grad():
        logits = model(images)
        loss = criterion(logits, masks)

    print("=" * 60)
    print(f"Config: {config_path}")
    print("images:", images.shape)
    print("masks:", masks.shape)
    print("logits:", logits.shape)
    print("loss:", loss.item())


def main():
    test_loss("configs/unet_ce.yaml")
    test_loss("configs/unet_dice.yaml")
    test_loss("configs/unet_ce_dice.yaml")


if __name__ == "__main__":
    main()