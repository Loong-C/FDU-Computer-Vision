import json
import os
import pandas as pd


def main():
    result_dir = "./results"
    rows = []

    for filename in os.listdir(result_dir):
        if not filename.endswith("_summary.json"):
            continue

        if filename.endswith("_train_summary.json"):
            continue

        path = os.path.join(result_dir, filename)

        with open(path, "r", encoding="utf-8") as f:
            summary = json.load(f)

        rows.append(summary)

    if len(rows) == 0:
        print("No summary files found.")
        return

    df = pd.DataFrame(rows)

    output_path = os.path.join(result_dir, "experiment_summary.csv")
    df.to_csv(output_path, index=False, encoding="utf-8-sig")

    print("Saved experiment summary to:", output_path)
    print(df)


if __name__ == "__main__":
    main()