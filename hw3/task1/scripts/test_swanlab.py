import random
import swanlab

run = swanlab.init(
    project="cv-hw3-task1",
    experiment_name="swanlab_test",
    config={
        "purpose": "test experiment tracking before real training",
        "epochs": 5,
    },
)

for epoch in range(5):
    loss = 1.0 / (epoch + 1) + random.random() * 0.05
    metric = epoch / 5 + random.random() * 0.02
    swanlab.log({
        "test/loss": loss,
        "test/metric": metric,
        "epoch": epoch,
    })

swanlab.finish()