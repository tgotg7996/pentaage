import { client } from "./client";
import type { ApiResponse } from "../types/api";
import type { FormulaAnalyzeRequest, FormulaAnalyzeResponse } from "../types/formula";

export async function analyzeFormula(
  payload: FormulaAnalyzeRequest
): Promise<ApiResponse<FormulaAnalyzeResponse>> {
  const response = await fetch(`${client.baseURL}/formulas/analyze`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error(`HTTP_${response.status}`);
  }

  return (await response.json()) as ApiResponse<FormulaAnalyzeResponse>;
}
