import torch
import torch.nn as nn
import torch.nn.functional as F


class DoubleConv(nn.Module):
    """
    Two consecutive convolution layers:
    Conv2d -> BatchNorm2d -> ReLU -> Conv2d -> BatchNorm2d -> ReLU
    """

    def __init__(self, in_channels: int, out_channels: int):
        super().__init__()

        self.double_conv = nn.Sequential(
            nn.Conv2d(
                in_channels,
                out_channels,
                kernel_size=3,
                padding=1,
                bias=False,
            ),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),

            nn.Conv2d(
                out_channels,
                out_channels,
                kernel_size=3,
                padding=1,
                bias=False,
            ),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),
        )

    def forward(self, x):
        return self.double_conv(x)


class Down(nn.Module):
    """
    Downsampling block:
    MaxPool2d -> DoubleConv
    """

    def __init__(self, in_channels: int, out_channels: int):
        super().__init__()

        self.down = nn.Sequential(
            nn.MaxPool2d(kernel_size=2, stride=2),
            DoubleConv(in_channels, out_channels),
        )

    def forward(self, x):
        return self.down(x)


class Up(nn.Module):
    """
    Upsampling block:
    ConvTranspose2d -> concatenate skip connection -> DoubleConv
    """

    def __init__(self, in_channels: int, skip_channels: int, out_channels: int):
        super().__init__()

        self.up = nn.ConvTranspose2d(
            in_channels,
            out_channels,
            kernel_size=2,
            stride=2,
        )

        self.conv = DoubleConv(
            in_channels=out_channels + skip_channels,
            out_channels=out_channels,
        )

    def forward(self, x, skip):
        x = self.up(x)

        if x.shape[-2:] != skip.shape[-2:]:
            x = F.interpolate(
                x,
                size=skip.shape[-2:],
                mode="bilinear",
                align_corners=False,
            )

        x = torch.cat([skip, x], dim=1)
        x = self.conv(x)

        return x


class OutConv(nn.Module):
    """
    Final 1x1 convolution layer.
    It maps feature channels to class logits.
    """

    def __init__(self, in_channels: int, num_classes: int):
        super().__init__()

        self.conv = nn.Conv2d(
            in_channels,
            num_classes,
            kernel_size=1,
        )

    def forward(self, x):
        return self.conv(x)


class UNet(nn.Module):
    """
    U-Net for semantic segmentation.

    Input:
        x: [B, 3, H, W]

    Output:
        logits: [B, num_classes, H, W]
    """

    def __init__(
        self,
        in_channels: int = 3,
        num_classes: int = 3,
        base_channels: int = 64,
    ):
        super().__init__()

        self.in_conv = DoubleConv(in_channels, base_channels)

        self.down1 = Down(base_channels, base_channels * 2)
        self.down2 = Down(base_channels * 2, base_channels * 4)
        self.down3 = Down(base_channels * 4, base_channels * 8)
        self.down4 = Down(base_channels * 8, base_channels * 16)

        self.up1 = Up(
            in_channels=base_channels * 16,
            skip_channels=base_channels * 8,
            out_channels=base_channels * 8,
        )

        self.up2 = Up(
            in_channels=base_channels * 8,
            skip_channels=base_channels * 4,
            out_channels=base_channels * 4,
        )

        self.up3 = Up(
            in_channels=base_channels * 4,
            skip_channels=base_channels * 2,
            out_channels=base_channels * 2,
        )

        self.up4 = Up(
            in_channels=base_channels * 2,
            skip_channels=base_channels,
            out_channels=base_channels,
        )

        self.out_conv = OutConv(base_channels, num_classes)

    def forward(self, x):
        x1 = self.in_conv(x)

        x2 = self.down1(x1)
        x3 = self.down2(x2)
        x4 = self.down3(x3)
        x5 = self.down4(x4)

        x = self.up1(x5, x4)
        x = self.up2(x, x3)
        x = self.up3(x, x2)
        x = self.up4(x, x1)

        logits = self.out_conv(x)

        return logits


if __name__ == "__main__":
    model = UNet(
        in_channels=3,
        num_classes=3,
        base_channels=64,
    )

    x = torch.randn(2, 3, 256, 256)
    y = model(x)

    print("Input shape:", x.shape)
    print("Output shape:", y.shape)