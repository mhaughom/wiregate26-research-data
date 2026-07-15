# Incident ball-track CSV schema

The file has a header and four required columns:

| Column | Type | Unit | Meaning |
| --- | --- | --- | --- |
| `ts_ms` | integer | Unix milliseconds | Source timestamp; strictly increasing |
| `x` | number | normalized pitch length | Multiply by 105.03 metres |
| `y` | number | normalized pitch width | Multiply by 68.03 metres |
| `z` | number | metres | Delivered ball height |

The verifier enforces the header, row count, finite values, increasing time,
declared endpoints and duration, normalized horizontal bounds, and a broad
physical height bound.
