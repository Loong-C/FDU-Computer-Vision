import torch
import torch.nn as nn
from torchvision import models
from torchvision.models.resnet import ResNet
from torchvision.models.resnet import conv1x1, conv3x3

from src.attention import SEBlock


class SEBasicBlock(nn.Module):
    expansion = 1

    def __init__(
        self,
        inplanes,
        planes,
        stride=1,
        downsample=None,
        groups=1,
        base_width=64,
        dilation=1,
        norm_layer=None,
        reduction=16
    ):
        super().__init__()

        if norm_layer is None:
            norm_layer = nn.BatchNorm2d

        if groups != 1 or base_width != 64:
            raise ValueError(
                "SEBasicBlock only supports groups=1 and base_width=64."
            )

        if dilation > 1:
            raise NotImplementedError(
                "Dilation > 1 is not supported in SEBasicBlock."
            )

        self.conv1 = conv3x3(inplanes, planes, stride)
        self.bn1 = norm_layer(planes)
        self.relu = nn.ReLU(inplace=True)

        self.conv2 = conv3x3(planes, planes)
        self.bn2 = norm_layer(planes)

        self.se = SEBlock(
            channels=planes * self.expansion,
            reduction=reduction
        )

        self.downsample = downsample
        self.stride = stride

    def forward(self, x):
        identity = x

        out = self.conv1(x)
        out = self.bn1(out)
        out = self.relu(out)

        out = self.conv2(out)
        out = self.bn2(out)

        out = self.se(out)

        if self.downsample is not None:
            identity = self.downsample(x)

        out = out + identity
        out = self.relu(out)

        return out


def build_resnet18_se(
    num_classes: int = 37,
    pretrained: bool = True,
    reduction: int = 16
):
    model = ResNet(
        block=SEBasicBlock,
        layers=[2, 2, 2, 2],
        num_classes=num_classes
    )

    if pretrained:
        pretrained_model = models.resnet18(
            weights=models.ResNet18_Weights.IMAGENET1K_V1
        )

        pretrained_state_dict = pretrained_model.state_dict()
        model_state_dict = model.state_dict()

        matched_state_dict = {}

        for name, param in pretrained_state_dict.items():
            if name in model_state_dict:
                if model_state_dict[name].shape == param.shape:
                    matched_state_dict[name] = param

        model_state_dict.update(matched_state_dict)
        model.load_state_dict(model_state_dict)

        print(
            f"Loaded {len(matched_state_dict)} pretrained parameters "
            f"from ImageNet ResNet-18."
        )
        print(
            "SE-block parameters and the final classifier are initialized "
            "randomly."
        )

    in_features = model.fc.in_features
    model.fc = nn.Linear(in_features, num_classes)

    return model


if __name__ == "__main__":
    model = build_resnet18_se(
        num_classes=37,
        pretrained=True,
        reduction=16
    )

    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(
        p.numel() for p in model.parameters() if p.requires_grad
    )

    print(model)
    print("Total parameters:", total_params)
    print("Trainable parameters:", trainable_params)
    print("Final classifier:", model.fc)

    dummy_input = torch.randn(2, 3, 224, 224)
    dummy_output = model(dummy_input)

    print("Dummy output shape:", dummy_output.shape)