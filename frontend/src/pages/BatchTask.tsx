import { type FormEvent, useEffect, useState, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";

import { getBatchDownloadUrl, getBatchStatus, submitBatch } from "../api/batch";
import type { BatchStatusResponse, BatchSubmitResponse } from "../types/batch";

import ProgressBar from "../components/ProgressBar";
import LoadingSpinner from "../components/LoadingSpinner";
import ErrorCard from "../components/ErrorCard";

export default function BatchTask() {
  const [csvText, setCsvText] = useState("smiles\nCCO");
  const [isDragging, setIsDragging] = useState(false);
  
  const [loading, setLoading] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  
  const [result, setResult] = useState<BatchSubmitResponse | null>(null);
  const [status, setStatus] = useState<BatchStatusResponse | null>(null);
  const [pollingError, setPollingError] = useState<string | null>(null);
  
  const fileInputRef = useRef<HTMLInputElement>(null);

  // 轮询逻辑
  useEffect(() => {
    if (!result?.job_id) return;

    let timer: number | null = null;
    let stopped = false;

    const poll = async () => {
      try {
        const data = await getBatchStatus(result.job_id);
        if (stopped) return;
        
        setStatus(data);
        
        if (data.status === "pending" || data.status === "running") {
           timer = window.setTimeout(poll, 3000);
           return;
        }
      } catch {
        if (!stopped) {
          setPollingError("轮询状态失败，请稍后重试");
        }
      }
    };

    void poll();

    return () => {
      stopped = true;
      if (timer !== null) window.clearTimeout(timer);
    };
  }, [result?.job_id]);

  const validateCsv = (text: string) => {
    const firstLine = text.trim().split("\n")[0];
    if (!firstLine || !firstLine.toLowerCase().includes("smiles")) {
      return "CSV 首行必须包含 'smiles' 列头";
    }
    return null;
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    
    const reader = new FileReader();
    reader.onload = (event) => {
      if (typeof event.target?.result === "string") {
        setCsvText(event.target.result);
      }
    };
    reader.readAsText(file);
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitError(null);
    setPollingError(null);

    const validationError = validateCsv(csvText);
    if (validationError) {
      setSubmitError(validationError);
      return;
    }

    setLoading(true);
    try {
      const data = await submitBatch(csvText);
      setResult(data);
      setStatus({ job_id: data.job_id, status: data.status, progress: { total: data.total_count, success: 0, failed: 0 } });
    } catch {
      setResult(null);
      setSubmitError("提交失败，请确认后端 batch 接口可用");
    } finally {
      setLoading(false);
    }
  }

  const getStatusColor = (s?: string) => {
    switch(s) {
      case "completed": return "var(--color-success)";
      case "failed": return "var(--color-error)";
      case "running": return "var(--color-primary)";
      case "pending": return "var(--color-text-secondary)";
      default: return "var(--color-text-secondary)";
    }
  };

  const getStatusLabel = (s?: string) => {
    switch(s) {
      case "completed": return "已完成";
      case "failed": return "失败";
      case "running": return "运行中";
      case "pending": return "排队中";
      default: return "未知";
    }
  };

  return (
    <div className="page-container">
      <h2 className="page-title">批量任务</h2>
      <div className="grid-layout-equal">
        
        {/* 左侧表单 */}
        <div className="card" style={{ alignSelf: "start" }}>
          <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "var(--space-md)" }}>
            
            <div>
              <label className="label">CSV 数据</label>
              
              <div 
                style={{
                  border: `2px dashed ${isDragging ? "var(--color-primary)" : "var(--color-border)"}`,
                  background: isDragging ? "var(--color-primary-light)" : "var(--color-bg)",
                  borderRadius: "var(--radius-md)",
                  padding: "var(--space-xl) var(--space-md)",
                  textAlign: "center",
                  marginBottom: "var(--space-sm)",
                  transition: "all var(--transition-fast)",
                  cursor: "pointer"
                }}
                onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
                onDragLeave={() => setIsDragging(false)}
                onDrop={(e) => {
                  e.preventDefault();
                  setIsDragging(false);
                  const file = e.dataTransfer.files?.[0];
                  if (file) {
                    const reader = new FileReader();
                    reader.onload = (event) => {
                      if (typeof event.target?.result === "string") {
                        setCsvText(event.target.result);
                      }
                    };
                    reader.readAsText(file);
                  }
                }}
                onClick={() => fileInputRef.current?.click()}
              >
                <div style={{ fontSize: "2rem", marginBottom: "var(--space-sm)" }}>📄</div>
                <div style={{ fontWeight: 500 }}>点击选择文件或拖拽到此处</div>
                <div style={{ fontSize: "var(--text-sm)", color: "var(--color-text-secondary)", marginTop: "4px" }}>
                  支持 .csv 格式
                </div>
                <input 
                  type="file" 
                  accept=".csv" 
                  style={{ display: "none" }} 
                  ref={fileInputRef}
                  onChange={handleFileChange}
                />
              </div>

              <div style={{ fontSize: "var(--text-sm)", color: "var(--color-text-secondary)", textAlign: "center", margin: "var(--space-sm) 0" }}>
                — 或直接粘贴内容 —
              </div>

              <textarea
                className="input"
                rows={6}
                value={csvText}
                onChange={(event) => setCsvText(event.target.value)}
                style={{ fontFamily: "var(--font-mono)", fontSize: "var(--text-sm)" }}
                placeholder="smiles&#10;CCO"
              />
            </div>

            <button type="submit" className="btn btn-primary" disabled={loading} style={{ marginTop: "var(--space-sm)" }}>
              {loading ? <LoadingSpinner text="提交中..." /> : "提交批量任务"}
            </button>
          </form>
          
          {submitError && (
            <div style={{ marginTop: "var(--space-md)" }}>
              <ErrorCard message={submitError} />
            </div>
          )}
        </div>

        {/* 右侧状态 */}
        <div>
          <AnimatePresence>
            {result && status && (
              <motion.div 
                initial={{ opacity: 0, y: 10 }} 
                animate={{ opacity: 1, y: 0 }}
                className="card"
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "var(--space-lg)" }}>
                  <h3 style={{ fontSize: "var(--text-lg)", fontWeight: 600 }}>任务状态</h3>
                  <span style={{ 
                    padding: "4px 12px", 
                    borderRadius: "var(--radius-full)", 
                    fontSize: "var(--text-sm)", 
                    fontWeight: 600,
                    color: getStatusColor(status.status),
                    background: `color-mix(in srgb, ${getStatusColor(status.status)} 15%, transparent)`
                  }}>
                    {getStatusLabel(status.status)}
                  </span>
                </div>

                <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-md)" }}>
                  <div>
                    <span className="label">Job ID</span>
                    <code style={{ fontFamily: "var(--font-mono)", fontSize: "var(--text-sm)", background: "var(--color-bg)", padding: "4px 8px", borderRadius: "4px", display: "inline-block", wordBreak: "break-all" }}>
                      {result.job_id}
                    </code>
                  </div>

                  <div>
                    <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "4px" }}>
                      <span className="label" style={{ marginBottom: 0 }}>分析进度</span>
                      <span style={{ fontSize: "var(--text-sm)", color: "var(--color-text-secondary)" }}>
                        {status.progress.success + status.progress.failed} / {status.progress.total}
                      </span>
                    </div>
                    <ProgressBar 
                      value={status.progress.success + status.progress.failed} 
                      max={status.progress.total} 
                      color={status.status === "failed" ? "var(--color-error)" : "var(--color-primary)"} 
                    />
                  </div>

                  {status.eta_seconds !== undefined && status.status === "running" && (
                     <div style={{ fontSize: "var(--text-sm)", color: "var(--color-text-secondary)" }}>
                       预计剩余时间: <span style={{ fontWeight: 600, color: "var(--color-text)" }}>{status.eta_seconds} 秒</span>
                     </div>
                  )}

                  {pollingError && (
                    <div style={{ color: "var(--color-error)", fontSize: "var(--text-sm)", marginTop: "var(--space-sm)" }}>
                      ⚠️ {pollingError}
                    </div>
                  )}

                  {status.status === "completed" && (
                    <a 
                      href={getBatchDownloadUrl(result.job_id)} 
                      target="_blank" 
                      rel="noreferrer"
                      className="btn"
                      style={{ 
                        marginTop: "var(--space-md)", 
                        background: "var(--color-success)", 
                        color: "#fff",
                        textDecoration: "none",
                        textAlign: "center"
                      }}
                    >
                      ⬇️ 下载结果 CSV
                    </a>
                  )}

                  {status.status === "failed" && (
                    <div style={{ marginTop: "var(--space-md)" }}>
                      <ErrorCard title="任务执行失败" message="后端处理过程中发生错误，请检查输入数据格式并重试。" />
                    </div>
                  )}
                </div>
              </motion.div>
            )}
            
            {!result && !submitError && (
               <div style={{ 
                 height: "100%", 
                 display: "flex", 
                 alignItems: "center", 
                 justifyContent: "center",
                 color: "var(--color-text-secondary)",
                 opacity: 0.5,
                 border: "2px dashed var(--color-border)",
                 borderRadius: "var(--radius-lg)"
               }}>
                 提交任务后在这里查看状态
               </div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}
