export interface FormulaIngredient {
  name: string;
  weight?: number;
}

export interface FormulaAnalyzeOptions {
  top_n?: number;
}

export interface FormulaAnalyzeRequest {
  formula_name: string;
  ingredients: FormulaIngredient[];
  options?: FormulaAnalyzeOptions;
}

export interface FormulaComponentScore {
  ingredient_name: string;
  total_score: number;
  resolved: boolean;
}

export interface FormulaAnalyzeResponse {
  total_score: number;
  component_scores: FormulaComponentScore[];
  synergy_bonus: number;
  unresolved_ingredients: string[];
}
