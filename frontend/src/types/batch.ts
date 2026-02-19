export interface BatchSubmitResponse {
  job_id: string;
  status: string;
  total_count: number;
}

export interface BatchProgress {
  total: number;
  success: number;
  failed: number;
}

export interface BatchStatusResponse {
  job_id: string;
  status: string;
  progress: BatchProgress;
  eta_seconds?: number;
}
