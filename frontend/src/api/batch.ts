import { client } from "./client";
import type { BatchStatusResponse, BatchSubmitResponse } from "../types/batch";

export async function submitBatch(csvText: string, options: Record<string, unknown> = {}): Promise<BatchSubmitResponse> {
  const formData = new FormData();
  const file = new File([csvText], "batch.csv", { type: "text/csv" });
  formData.append("file", file);
  formData.append("options", JSON.stringify(options));

  const response = await fetch(`${client.baseURL}/batch/submit`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    throw new Error(`HTTP_${response.status}`);
  }

  return (await response.json()) as BatchSubmitResponse;
}

export async function getBatchStatus(jobId: string): Promise<BatchStatusResponse> {
  const response = await fetch(`${client.baseURL}/batch/${jobId}/status`);

  if (!response.ok) {
    throw new Error(`HTTP_${response.status}`);
  }

  return (await response.json()) as BatchStatusResponse;
}

export function getBatchDownloadUrl(jobId: string): string {
  return `${client.baseURL}/batch/${jobId}/download`;
}
