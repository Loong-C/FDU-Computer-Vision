import torch
import torch.nn as nn
import torch.nn.functional as F


class DiceLoss(nn.Module):
    """
    Multi-class Dice Loss for semantic segmentation.

    logits shape:
        [B, C, H, W]

    targets shape:
        [B, H, W]

    targets values:
        0, 1, ..., C - 1
    """

    def __init__(self, num_classes: int, smooth: float = 1e-6):
        super().__init__()

        self.num_classes = num_classes
        self.smooth = smooth

    def forward(self, logits, targets):
        probs = torch.softmax(logits, dim=1)

        targets_one_hot = F.one_hot(
            targets,
            num_classes=self.num_classes,
        )

        targets_one_hot = targets_one_hot.permute(0, 3, 1, 2).float()

        dims = (0, 2, 3)

        intersection = torch.sum(probs * targets_one_hot, dim=dims)
        cardinality = torch.sum(probs + targets_one_hot, dim=dims)

        dice_score = (2.0 * intersection + self.smooth) / (
            cardinality + self.smooth
        )

        dice_loss = 1.0 - dice_score.mean()

        return dice_loss


class CombinedLoss(nn.Module):
    """
    Cross Entropy Loss + Dice Loss.
    """

    def __init__(
        self,
        num_classes: int,
        ce_weight: float = 1.0,
        dice_weight: float = 1.0,
    ):
        super().__init__()

        self.ce_weight = ce_weight
        self.dice_weight = dice_weight

        self.ce_loss = nn.CrossEntropyLoss()
        self.dice_loss = DiceLoss(num_classes=num_classes)

    def forward(self, logits, targets):
        ce = self.ce_loss(logits, targets)
        dice = self.dice_loss(logits, targets)

        return self.ce_weight * ce + self.dice_weight * dice


def build_loss(config: dict):
    loss_type = config["train"]["loss_type"]
    num_classes = config["model"]["num_classes"]

    if loss_type == "ce":
        return nn.CrossEntropyLoss()

    if loss_type == "dice":
        return DiceLoss(num_classes=num_classes)

    if loss_type == "ce_dice":
        return CombinedLoss(num_classes=num_classes)

    raise ValueError(f"Unsupported loss type: {loss_type}")