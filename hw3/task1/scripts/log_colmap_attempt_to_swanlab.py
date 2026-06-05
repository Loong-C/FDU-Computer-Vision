import argparse
import swanlab


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--attempt_name", type=str, required=True)
    parser.add_argument("--num_images", type=int, required=True)
    parser.add_argument("--num_registered_images", type=int, required=True)
    parser.add_argument("--num_sparse_points", type=int, required=True)
    parser.add_argument("--num_observations", type=int, required=True)
    parser.add_argument("--mean_track_length", type=float, required=True)
    parser.add_argument("--mean_observations_per_image", type=float, required=True)
    parser.add_argument("--mean_reprojection_error", type=float, required=True)
    parser.add_argument("--success", type=int, required=True)
    parser.add_argument("--note", type=str, default="")
    args = parser.parse_args()

    swanlab.init(
        project="cv-hw3-task1",
        experiment_name=args.attempt_name,
        config={
            "stage": "object_a_colmap",
            "method": "COLMAP sparse reconstruction",
            "note": args.note,
        },
    )

    swanlab.log({
        "colmap/images": args.num_images,
        "colmap/registered_images": args.num_registered_images,
        "colmap/sparse_points": args.num_sparse_points,
        "colmap/observations": args.num_observations,
        "colmap/mean_track_length": args.mean_track_length,
        "colmap/mean_observations_per_image": args.mean_observations_per_image,
        "colmap/mean_reprojection_error_px": args.mean_reprojection_error,
        "colmap/success": args.success,
        "colmap/registration_rate": args.num_registered_images / args.num_images,
    })

    swanlab.finish()


if __name__ == "__main__":
    main()