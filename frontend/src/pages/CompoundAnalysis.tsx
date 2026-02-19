import { type FormEvent, useState } from "react";

import { analyzeCompound } from "../api/compounds";
import type { CompoundAnalyzeResponse } from "../types/compound";

export default function CompoundAnalysis() {
  const [smiles, setSmiles] = useState("CCO");
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
    <section>
      <h2>Compound Analysis</h2>
      <form onSubmit={handleSubmit} style={{ display: "grid", gap: "8px", maxWidth: "480px" }}>
        <label htmlFor="smiles-input">SMILES</label>
        <input
          id="smiles-input"
          type="text"
          value={smiles}
          onChange={(event) => setSmiles(event.target.value)}
          placeholder="例如: CCO"
        />
        <button type="submit" disabled={loading}>
          {loading ? "分析中..." : "开始分析"}
        </button>
      </form>

      {error ? <p style={{ color: "#b91c1c" }}>{error}</p> : null}

      {result ? (
        <div style={{ marginTop: "16px" }}>
          <p>总分: {result.total_score}</p>
          <p>canonical_smiles: {result.canonical_smiles}</p>
          <p>cached: {String(result.cached)}</p>
          <p>calc_id: {result.calc_id}</p>
        </div>
      ) : null}
    </section>
  );
}
