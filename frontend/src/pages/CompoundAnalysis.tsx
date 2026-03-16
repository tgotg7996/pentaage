import { type FormEvent, useState } from "react";
import { motion } from "framer-motion";

import { analyzeCompound } from "../api/compounds";
import type { CompoundAnalyzeResponse } from "../types/compound";

import ScoreCircle from "../components/ScoreCircle";
import ProgressBar from "../components/ProgressBar";
import LoadingSpinner from "../components/LoadingSpinner";
import ErrorCard from "../components/ErrorCard";

export default function CompoundAnalysis() {
  const [smiles, setSmiles] = useState("CCO");
  
  // 高级选项
  const [radius, setRadius] = useState(2);
  const [nBits, setNBits] = useState(2048);
  const [useFeatures, setUseFeatures] = useState(false);
  const [topN, setTopN] = useState(5);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<CompoundAnalyzeResponse | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const response = await analyzeCompound({
        input_type: "smiles",
        input_value: smiles,
        options: {
          radius,
          n_bits: nBits,
          use_features: useFeatures,
          top_n: topN,
        },
      });

      if (!response.success || !response.data) {
        setResult(null);
        setError(response.error?.message ?? "分析失败");
        return;
      }

      setResult(response.data);
    } catch {
      setResult(null);
      setError("请求失败，请确认后端已启动");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="page-container">
      <h2 className="page-title">单体分析</h2>
      <div className="grid-layout">
        
        {/* 左侧表单 */}
        <div className="card" style={{ alignSelf: "start" }}>
          <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "var(--space-md)" }}>
            <div>
              <label htmlFor="smiles-input" className="label">SMILES 字符串</label>
              <input
                id="smiles-input"
                className="input"
                type="text"
                value={smiles}
                onChange={(event) => setSmiles(event.target.value)}
                placeholder="例如: CCO"
                required
              />
            </div>
            
            <details style={{ fontSize: "var(--text-sm)" }}>
              <summary style={{ cursor: "pointer", color: "var(--color-primary)", fontWeight: 500, marginBottom: "var(--space-sm)" }}>
                高级选项
              </summary>
              <div style={{ display: "grid", gap: "var(--space-sm)", marginTop: "var(--space-xs)", paddingLeft: "12px", borderLeft: "2px solid var(--color-border)" }}>
                <div>
                  <label className="label">Radius</label>
                  <input className="input" type="number" value={radius} onChange={(e) => setRadius(Number(e.target.value))} min={1} max={5} />
                </div>
                <div>
                  <label className="label">n_bits</label>
                  <select className="input" value={nBits} onChange={(e) => setNBits(Number(e.target.value))}>
                    <option value={1024}>1024</option>
                    <option value={2048}>2048</option>
                    <option value={4096}>4096</option>
                  </select>
                </div>
                <div>
                  <label className="label">use_features</label>
                  <select className="input" value={useFeatures ? "true" : "false"} onChange={(e) => setUseFeatures(e.target.value === "true")}>
                    <option value="false">False</option>
                    <option value="true">True</option>
                  </select>
                </div>
                <div>
                  <label className="label">Top N</label>
                  <input className="input" type="number" value={topN} onChange={(e) => setTopN(Number(e.target.value))} min={1} max={20} />
                </div>
              </div>
            </details>

            <button type="submit" className="btn btn-primary" disabled={loading} style={{ marginTop: "var(--space-sm)" }}>
              {loading ? <LoadingSpinner text="分析中..." /> : "开始分析"}
            </button>
          </form>
        </div>

        {/* 右侧结果 */}
        <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-lg)" }}>
          {error && (
            <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
              <ErrorCard message={error} />
            </motion.div>
          )}

          {result && (
            <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="card">
              <div style={{ display: "flex", gap: "var(--space-xl)", alignItems: "center", marginBottom: "var(--space-lg)" }}>
                <ScoreCircle score={result.total_score} label="综合得分" />
                <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: "var(--space-sm)" }}>
                  <div>
                    <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "4px" }}>
                      <span className="label">基础分 (满分60)</span>
                      <span style={{ fontWeight: 600 }}>{result.base_score.toFixed(1)}</span>
                    </div>
                    <ProgressBar value={result.base_score} max={60} showLabel={false} color="var(--color-primary)" />
                  </div>
                  <div>
                    <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "4px" }}>
                      <span className="label">协同分 (满分40)</span>
                      <span style={{ fontWeight: 600 }}>{result.composite_score.toFixed(1)}</span>
                    </div>
                    <ProgressBar value={result.composite_score} max={40} showLabel={false} color="var(--color-accent)" />
                  </div>
                  <div style={{ marginTop: "8px", fontSize: "var(--text-sm)", color: "var(--color-text-secondary)" }}>
                    标准化 SMILES: <code style={{ fontFamily: "var(--font-mono)", background: "var(--color-border)", padding: "2px 6px", borderRadius: "4px" }}>{result.canonical_smiles}</code>
                  </div>
                </div>
              </div>

              <h3 style={{ fontSize: "var(--text-lg)", marginBottom: "var(--space-md)", borderBottom: "1px solid var(--color-border)", paddingBottom: "var(--space-sm)" }}>相似中药成分 Top {result.top_similarities.length}</h3>
              <div style={{ overflowX: "auto" }}>
                <table style={{ width: "100%", textAlign: "left", fontSize: "var(--text-sm)" }}>
                  <thead>
                    <tr style={{ color: "var(--color-text-secondary)", borderBottom: "1px solid var(--color-border)" }}>
                      <th style={{ padding: "8px" }}>排名</th>
                      <th style={{ padding: "8px" }}>名称 (CAS)</th>
                      <th style={{ padding: "8px", width: "40%" }}>相似度</th>
                    </tr>
                  </thead>
                  <tbody>
                    {result.top_similarities.map((item) => (
                      <tr key={item.reference_cas} style={{ borderBottom: "1px solid var(--color-border)" }}>
                        <td style={{ padding: "12px 8px" }}>#{item.rank}</td>
                        <td style={{ padding: "12px 8px", fontWeight: 500 }}>
                          {item.reference_name}
                          <div style={{ fontSize: "var(--text-xs)", color: "var(--color-text-secondary)", fontWeight: 400 }}>{item.reference_cas}</div>
                        </td>
                        <td style={{ padding: "12px 8px" }}>
                          <ProgressBar value={item.similarity} max={1} />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              
              <div style={{ marginTop: "var(--space-lg)", fontSize: "var(--text-xs)", color: "var(--color-text-secondary)", display: "flex", gap: "var(--space-md)", flexWrap: "wrap", opacity: 0.7 }}>
                <span>算法版本: {result.algorithm_version}</span>
                <span>耗时: {result.processing_time_ms ? `${result.processing_time_ms}ms` : '未知'}</span>
                <span>缓存: {result.cached ? '开启' : '关闭'}</span>
                <span>calc_id: {result.calc_id.slice(0, 8)}...</span>
              </div>
            </motion.div>
          )}
        </div>
      </div>
    </div>
  );
}
