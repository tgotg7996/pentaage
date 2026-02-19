import { type FormEvent, useState } from "react";

import { analyzeFormula } from "../api/formulas";
import type { FormulaAnalyzeResponse } from "../types/formula";

export default function FormulaAnalysis() {
  const [formulaName, setFormulaName] = useState("Demo Formula");
  const [ingredientsText, setIngredientsText] = useState("Resveratrol\nQuercetin");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<FormulaAnalyzeResponse | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError(null);

    const ingredients = ingredientsText
      .split("\n")
      .map((item) => item.trim())
      .filter((item) => item.length > 0)
      .map((name) => ({ name }));

    try {
      const response = await analyzeFormula({
        formula_name: formulaName,
        ingredients,
      });

      if (!response.success || !response.data) {
        setResult(null);
        setError(response.error?.message ?? "分析失败");
        return;
      }

      setResult(response.data);
    } catch {
      setResult(null);
      setError("请求失败，请确认后端方子分析接口可用");
    } finally {
      setLoading(false);
    }
  }

  return (
    <section>
      <h2>Formula Analysis</h2>
      <form onSubmit={handleSubmit} style={{ display: "grid", gap: "8px", maxWidth: "560px" }}>
        <label htmlFor="formula-name">方子名</label>
        <input
          id="formula-name"
          type="text"
          value={formulaName}
          onChange={(event) => setFormulaName(event.target.value)}
        />

        <label htmlFor="formula-ingredients">成分（每行一个）</label>
        <textarea
          id="formula-ingredients"
          rows={5}
          value={ingredientsText}
          onChange={(event) => setIngredientsText(event.target.value)}
        />

        <button type="submit" disabled={loading}>
          {loading ? "分析中..." : "开始分析"}
        </button>
      </form>

      {error ? <p style={{ color: "#b91c1c" }}>{error}</p> : null}

      {result ? (
        <div style={{ marginTop: "16px" }}>
          <p>总分: {result.total_score}</p>
          <p>协同加分: {result.synergy_bonus}</p>
          <p>未解析成分数: {result.unresolved_ingredients.length}</p>
          <p>成分评分条目: {result.component_scores.length}</p>
        </div>
      ) : null}
    </section>
  );
}
