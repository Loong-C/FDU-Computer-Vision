import torch
import torch.nn as nn
from src.resnet_se import build_resnet18_se
from torchvision import models


def build_resnet18(num_classes: int = 37, pretrained: bool = True):
    if pretrained:
        weights = models.ResNet18_Weights.IMAGENET1K_V1
    else:
        weights = None

    model = models.resnet18(weights=weights)

    in_features = model.fc.in_features
    model.fc = nn.Linear(in_features, num_classes)

    return model


def build_model(
    model_name: str = "resnet18",
    num_classes: int = 37,
    pretrained: bool = True,
    attention: str = "none"
):
    model_name = model_name.lower()
    attention = attention.lower()

    if model_name == "resnet18":
        if attention == "none":
            model = build_resnet18(
                num_classes=num_classes,
                pretrained=pretrained
            )
        elif attention == "se":
            model = build_resnet18_se(
                num_classes=num_classes,
                pretrained=pretrained,
                reduction=16
            )
        else:
            raise ValueError(
                f"Unsupported attention mode for ResNet-18: {attention}"
            )
    else:
        raise ValueError(f"Unsupported model name: {model_name}")

    return model


def build_param_groups(
    model: nn.Module,
    backbone_lr: float = 1e-4,
    classifier_lr: float = 1e-3,
    weight_decay: float = 1e-4
):
    backbone_params = []
    classifier_params = []

    for name, param in model.named_parameters():
        if not param.requires_grad:
            continue

        if name.startswith("fc."):
            classifier_params.append(param)
        else:
            backbone_params.append(param)

    param_groups = [
        {
            "params": backbone_params,
            "lr": backbone_lr,
            "weight_decay": weight_decay
        },
        {
            "params": classifier_params,
            "lr": classifier_lr,
            "weight_decay": weight_decay
        }
    ]

    return param_groups


if __name__ == "__main__":
    model = build_model(
        model_name="resnet18",
        num_classes=37,
        pretrained=True,
        attention="none"
    )

    print(model)

    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(
        p.numel() for p in model.parameters() if p.requires_grad
    )

    print("Total parameters:", total_params)
    print("Trainable parameters:", trainable_params)
    print("Final classifier:", model.fc)

    param_groups = build_param_groups(
        model,
        backbone_lr=1e-4,
        classifier_lr=1e-3,
        weight_decay=1e-4
    )

    print("Number of parameter groups:", len(param_groups))
    print("Backbone lr:", param_groups[0]["lr"])
    print("Classifier lr:", param_groups[1]["lr"])