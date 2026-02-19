export interface AnalyzeOptions {
  radius?: number;
  n_bits?: number;
  use_features?: boolean;
  top_n?: number;
}

export interface SimilarityResult {
  reference_name: string;
  reference_cas: string;
  similarity: number;
  rank: number;
}

export interface CompoundAnalyzeRequest {
  input_type: "smiles" | "name" | "cas" | "mol";
  input_value: string;
  options?: AnalyzeOptions;
}

export interface CompoundAnalyzeResponse {
  compound_name: string | null;
  canonical_smiles: string;
  total_score: number;
  base_score: number;
  composite_score: number;
  top_similarities: SimilarityResult[];
  algorithm_version: string;
  fingerprint_params: Record<string, unknown>;
  cached: boolean;
  calc_id: string;
}
