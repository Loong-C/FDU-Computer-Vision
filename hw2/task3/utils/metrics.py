import torch


class SegmentationMetric:
    """
    Metrics for multi-class semantic segmentation.

    It accumulates a confusion matrix over batches, then computes:
    - Pixel Accuracy
    - per-class IoU
    - mean IoU
    """

    def __init__(self, num_classes: int):
        self.num_classes = num_classes
        self.reset()

    def reset(self):
        self.confusion_matrix = torch.zeros(
            self.num_classes,
            self.num_classes,
            dtype=torch.int64,
        )

    @torch.no_grad()
    def update(self, logits, targets):
        """
        logits:
            [B, C, H, W]

        targets:
            [B, H, W]
        """

        preds = torch.argmax(logits, dim=1)

        preds = preds.detach().cpu().view(-1)
        targets = targets.detach().cpu().view(-1)

        valid_mask = (targets >= 0) & (targets < self.num_classes)

        targets = targets[valid_mask]
        preds = preds[valid_mask]

        indices = self.num_classes * targets + preds

        matrix = torch.bincount(
            indices,
            minlength=self.num_classes ** 2,
        ).reshape(self.num_classes, self.num_classes)

        self.confusion_matrix += matrix

    def compute_pixel_accuracy(self):
        correct = torch.diag(self.confusion_matrix).sum()
        total = self.confusion_matrix.sum()

        if total == 0:
            return 0.0

        return (correct.float() / total.float()).item()

    def compute_iou(self):
        intersection = torch.diag(self.confusion_matrix).float()

        ground_truth = self.confusion_matrix.sum(dim=1).float()
        prediction = self.confusion_matrix.sum(dim=0).float()

        union = ground_truth + prediction - intersection

        iou = intersection / torch.clamp(union, min=1.0)

        return iou

    def compute_miou(self):
        iou = self.compute_iou()

        valid = torch.sum(self.confusion_matrix, dim=1) > 0

        if valid.sum() == 0:
            return 0.0

        return iou[valid].mean().item()

    def get_results(self):
        pixel_acc = self.compute_pixel_accuracy()
        iou = self.compute_iou()
        miou = self.compute_miou()

        return {
            "pixel_acc": pixel_acc,
            "miou": miou,
            "class_iou": iou.tolist(),
        }


if __name__ == "__main__":
    metric = SegmentationMetric(num_classes=3)

    logits = torch.randn(2, 3, 256, 256)
    targets = torch.randint(0, 3, size=(2, 256, 256))

    metric.update(logits, targets)
    results = metric.get_results()

    print(results)