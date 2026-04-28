import os
import torch
import numpy as np
import matplotlib.pyplot as plt

from datasets.oxford_pet import build_dataloaders
from main import load_config
from models.unet import UNet


CONFIG_PATH = "configs/unet_ce_dice.yaml"
CHECKPOINT_PATH = "runs/unet_ce_dice_20260428_194303/best_model.pth"
SAVE_DIR = "results/predictions"


def denormalize(image):
    mean = torch.tensor([0.485, 0.456, 0.406]).view(3, 1, 1)
    std = torch.tensor([0.229, 0.224, 0.225]).view(3, 1, 1)

    image = image.cpu() * std + mean
    image = torch.clamp(image, 0, 1)

    return image


def mask_to_rgb(mask):
    mask = mask.cpu().numpy()

    color_map = np.array(
        [
            [255, 128, 128],
            [128, 255, 128],
            [128, 128, 255],
        ],
        dtype=np.uint8,
    )

    rgb = color_map[mask]

    return rgb


@torch.no_grad()
def main():
    os.makedirs(SAVE_DIR, exist_ok=True)

    config = load_config(CONFIG_PATH)
    device = torch.device(config["device"] if torch.cuda.is_available() else "cpu")

    _, val_loader = build_dataloaders(config)

    model = UNet(
        in_channels=config["model"]["in_channels"],
        num_classes=config["model"]["num_classes"],
        base_channels=config["model"]["base_channels"],
    ).to(device)

    checkpoint = torch.load(CHECKPOINT_PATH, map_location=device)
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()

    images, masks = next(iter(val_loader))

    images = images.to(device)
    logits = model(images)
    preds = torch.argmax(logits, dim=1).cpu()

    images = images.cpu()
    masks = masks.cpu()

    num_samples = min(6, images.size(0))

    for i in range(num_samples):
        image = denormalize(images[i]).permute(1, 2, 0).numpy()
        gt_mask = mask_to_rgb(masks[i])
        pred_mask = mask_to_rgb(preds[i])

        fig, axes = plt.subplots(1, 3, figsize=(10, 4))

        axes[0].imshow(image)
        axes[0].set_title("Image")
        axes[0].axis("off")

        axes[1].imshow(gt_mask)
        axes[1].set_title("Ground Truth")
        axes[1].axis("off")

        axes[2].imshow(pred_mask)
        axes[2].set_title("Prediction")
        axes[2].axis("off")

        plt.tight_layout()

        save_path = os.path.join(SAVE_DIR, f"prediction_{i + 1}.png")
        plt.savefig(save_path, dpi=300)
        plt.close()

    print(f"Prediction visualizations saved to {SAVE_DIR}")


if __name__ == "__main__":
    main()