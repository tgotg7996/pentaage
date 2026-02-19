export interface ApiResponse<T> {
  success: boolean;
  data: T | null;
  error: ApiError | null;
  request_id: string;
  processing_time_ms?: number;
}

export interface ApiError {
  code: string;
  message: string;
  details: Record<string, unknown>;
}
