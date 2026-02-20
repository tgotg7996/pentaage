import { type FormEvent, useEffect, useState } from "react";

import { getBatchDownloadUrl, getBatchStatus, submitBatch } from "../api/batch";
import type { BatchStatusResponse, BatchSubmitResponse } from "../types/batch";

export default function BatchTask() {
  const [csvText, setCsvText] = useState("smiles\nCCO");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<BatchSubmitResponse | null>(null);
  const [status, setStatus] = useState<BatchStatusResponse | null>(null);

  useEffect(() => {
    if (!result?.job_id) {
      return;
    }

    let timer: number | null = null;
    let stopped = false;

    const poll = async () => {
      try {
        const data = await getBatchStatus(result.job_id);
        if (stopped) {
          return;
        }
        setStatus(data);
        if (data.status === "pending" || data.status === "running") {
          timer = window.setTimeout(poll, 3000);
          return;
        }
        if (data.status === "failed") {
          setError("批量任务执行失败，请稍后重试或检查输入数据");
        }
      } catch {
        if (!stopped) {
          setError("轮询状态失败，请稍后重试");
        }
      }
    };

    void poll();

    return () => {
      stopped = true;
      if (timer !== null) {
        window.clearTimeout(timer);
      }
    };
  }, [result?.job_id]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const data = await submitBatch(csvText);
      setResult(data);
      setStatus(null);
    } catch {
      setResult(null);
      setError("提交失败，请确认后端 batch 接口可用");
    } finally {
      setLoading(false);
    }
  }

  return (
    <section>
      <h2>Batch Task</h2>
      <form onSubmit={handleSubmit} style={{ display: "grid", gap: "8px", maxWidth: "560px" }}>
        <label htmlFor="batch-csv">CSV 内容</label>
        <textarea
          id="batch-csv"
          rows={7}
          value={csvText}
          onChange={(event) => setCsvText(event.target.value)}
        />

        <button type="submit" disabled={loading}>
          {loading ? "提交中..." : "提交批量任务"}
        </button>
      </form>

      {error ? <p style={{ color: "#b91c1c" }}>{error}</p> : null}

      {result ? (
        <div style={{ marginTop: "16px" }}>
          <p>job_id: {result.job_id}</p>
          <p>status: {result.status}</p>
          <p>total_count: {result.total_count}</p>
          {status ? (
            <>
              <p>
                progress: {status.progress.success}/{status.progress.total}
              </p>
              <p>latest_status: {status.status}</p>
            </>
          ) : null}
          {status?.status === "completed" ? (
            <p>
              <a href={getBatchDownloadUrl(result.job_id)} target="_blank" rel="noreferrer">
                下载结果
              </a>
            </p>
          ) : null}
          {status?.status === "failed" ? <p style={{ color: "#b91c1c" }}>任务执行失败</p> : null}
        </div>
      ) : null}
    </section>
  );
}
