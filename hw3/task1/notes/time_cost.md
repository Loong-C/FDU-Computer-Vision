# Time Cost Record

| Part | Method | Device | Input Size / Iterations | Time Cost | Notes |
|---|---|---|---|---|---|
| Object A | COLMAP + 2DGS | Local CUDA GPU | 34 images / 30000 iterations | 4855.77 s | Clean formal 2DGS training run after COLMAP preparation |
| Background | 2DGS | Local CUDA GPU | 240 images / 30000 iterations at half resolution | 1368.52 s | Mip-NeRF 360 `counter` clean formal training run |
| Object B | Text-to-3D | TBD | TBD | TBD | threestudio SDS |
| Object C | Image-to-3D | TBD | TBD | TBD | Magic123 |
