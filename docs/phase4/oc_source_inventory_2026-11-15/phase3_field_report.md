# Habnetic Operations Center | Phase 3 source-field discovery

Source: read-only local scan. `FOUND` proves physical-path existence; schema requires pyarrow.

## DON

- **asset_metrics.parquet**: `FOUND`
  - Rows: **7755**; columns: `bldg_id`, `p_mean`, `p_std`, `topk_prob_k39`, `rank_std_k39`, `topk_prob_k78`, `rank_std_k78`, `topk_prob_k194`, `rank_std_k194`, `topk_prob_k1000`, `rank_std_k1000`, `topk_prob_k2500`, `rank_std_k2500`, `topk_prob_k5000`, `rank_std_k5000`
- **decision_metrics.json**: `FOUND`
  - JSON keys:
- **run_metadata.json**: `FOUND`
  - JSON keys: data_root, exposure_raw_cols, hazard_model_col, hazard_raw_cols, hazard_reference_median_mm, n_assets_reference, n_assets_target, output_file, phase, reference_city, scaler_cols, scaler_path, support_check_cols, support_diagnostics_csv, support_diagnostics_json, synthetic_outcome_alpha, synthetic_outcome_beta_e, synthetic_outcome_beta_h, synthetic_outcome_col, synthetic_outcome_seed, synthetic_probability_col, target_city
- **summary.json**: `FOUND`
  - JSON keys: alpha, beta_E, beta_H
- **support_diagnostics.json**: `FOUND`
  - JSON keys:
- **phase3_features_scaled.parquet**: `FOUND`
  - Rows: **7755**; columns: `bldg_id`, `dist_to_water_m`, `water_len_density_250m`, `water_len_density_500m`, `water_len_density_1000m`, `H_pluvial_v1_mm`, `dist_to_water_m_z`, `water_len_density_250m_z`, `water_len_density_500m_z`, `water_len_density_1000m_z`, `H_pluvial_v1_mm_z`, `E_hat_v0`, `H_pluvial_v1_rel`, `H_pluvial_v1_logrel`, `p_damage_true`, `Y_damage`

**M0 map readiness:** `FILE_AND_BASIC_SCHEMA_FOUND`; still validate selection semantics and the geometry join.

## RTM

- **asset_metrics.parquet**: `FOUND`
  - Rows: **221324**; columns: `bldg_id`, `p_mean`, `p_std`, `topk_prob_k1000`, `rank_std_k1000`, `topk_prob_k1107`, `rank_std_k1107`, `topk_prob_k2213`, `rank_std_k2213`, `topk_prob_k2500`, `rank_std_k2500`, `topk_prob_k5000`, `rank_std_k5000`, `topk_prob_k5533`, `rank_std_k5533`
- **decision_metrics.json**: `FOUND`
  - JSON keys:
- **run_metadata.json**: `FOUND`
  - JSON keys: data_root, exposure_raw_cols, hazard_model_col, hazard_raw_cols, hazard_reference_median_mm, n_assets_reference, n_assets_target, output_file, phase, reference_city, scaler_cols, scaler_path, support_check_cols, support_diagnostics_csv, support_diagnostics_json, synthetic_outcome_alpha, synthetic_outcome_beta_e, synthetic_outcome_beta_h, synthetic_outcome_col, synthetic_outcome_seed, synthetic_probability_col, target_city
- **summary.json**: `FOUND`
  - JSON keys: alpha, beta_E, beta_H
- **support_diagnostics.json**: `FOUND`
  - JSON keys:
- **phase3_features_scaled.parquet**: `FOUND`
  - Rows: **221324**; columns: `bldg_id`, `dist_to_water_m`, `water_len_density_250m`, `water_len_density_500m`, `water_len_density_1000m`, `H_pluvial_v1_mm`, `dist_to_water_m_z`, `water_len_density_250m_z`, `water_len_density_500m_z`, `water_len_density_1000m_z`, `H_pluvial_v1_mm_z`, `E_hat_v0`, `H_pluvial_v1_rel`, `H_pluvial_v1_logrel`, `p_damage_true`, `Y_damage`

**M0 map readiness:** `FILE_AND_BASIC_SCHEMA_FOUND`; still validate selection semantics and the geometry join.

## HAM

- **asset_metrics.parquet**: `FOUND`
  - Rows: **341530**; columns: `bldg_id`, `p_mean`, `p_std`, `topk_prob_k1000`, `rank_std_k1000`, `topk_prob_k1708`, `rank_std_k1708`, `topk_prob_k2500`, `rank_std_k2500`, `topk_prob_k3415`, `rank_std_k3415`, `topk_prob_k5000`, `rank_std_k5000`, `topk_prob_k8538`, `rank_std_k8538`
- **decision_metrics.json**: `FOUND`
  - JSON keys:
- **run_metadata.json**: `FOUND`
  - JSON keys: data_root, exposure_raw_cols, hazard_model_col, hazard_raw_cols, hazard_reference_median_mm, n_assets_reference, n_assets_target, output_file, phase, reference_city, scaler_cols, scaler_path, support_check_cols, support_diagnostics_csv, support_diagnostics_json, synthetic_outcome_alpha, synthetic_outcome_beta_e, synthetic_outcome_beta_h, synthetic_outcome_col, synthetic_outcome_seed, synthetic_probability_col, target_city
- **summary.json**: `FOUND`
  - JSON keys: alpha, beta_E, beta_H
- **support_diagnostics.json**: `FOUND`
  - JSON keys:
- **phase3_features_scaled.parquet**: `FOUND`
  - Rows: **341530**; columns: `bldg_id`, `dist_to_water_m`, `water_len_density_250m`, `water_len_density_500m`, `water_len_density_1000m`, `H_pluvial_v1_mm`, `dist_to_water_m_z`, `water_len_density_250m_z`, `water_len_density_500m_z`, `water_len_density_1000m_z`, `H_pluvial_v1_mm_z`, `E_hat_v0`, `H_pluvial_v1_rel`, `H_pluvial_v1_logrel`, `p_damage_true`, `Y_damage`

**M0 map readiness:** `FILE_AND_BASIC_SCHEMA_FOUND`; still validate selection semantics and the geometry join.

## Semantic warning

M1-G2 B0 is a synthetic within-city refit, **not** the original Phase 3/M0 result. A historical map needs original per-building decision data and historical run provenance.
