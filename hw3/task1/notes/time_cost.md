# Time Cost Record

| Part | Method | Device | Input Size / Iterations | Time Cost | Notes |
|---|---|---|---|---|---|
| Object A | COLMAP + 2DGS | Local CUDA GPU | 34 images / 30000 iterations | 4855.77 s | Clean formal 2DGS training run after COLMAP preparation |
| Background | 2DGS | Local CUDA GPU | 240 images / 30000 iterations at half resolution | 1368.52 s | Mip-NeRF 360 `counter` clean formal training run |
| Object B | threestudio DreamFusion SD SDS | Local CUDA GPU | 10000 iterations at 64 x 64 | 3624.22 s training + 35.46 s export | Formal run completed successfully; default isosurface threshold `25.0` exported 28180 vertices and 56536 faces |
| Object C | Magic123 | Local CUDA GPU | 5000 coarse + 5000 fine iterations | Pending | SD + Zero123 coarse NeRF and fine DMTet |
