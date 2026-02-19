import { client } from "./client";
import type { ApiResponse } from "../types/api";
import type { CompoundAnalyzeRequest, CompoundAnalyzeResponse } from "../types/compound";

export async function analyzeCompound(
  payload: CompoundAnalyzeRequest
): Promise<ApiResponse<CompoundAnalyzeResponse>> {
  const response = await fetch(`${client.baseURL}/compounds/analyze`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error(`HTTP_${response.status}`);
  }

  return (await response.json()) as ApiResponse<CompoundAnalyzeResponse>;
}
