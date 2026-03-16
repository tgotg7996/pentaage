import { type FormEvent, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";

import { analyzeFormula } from "../api/formulas";
import type { FormulaAnalyzeResponse } from "../types/formula";

import ScoreCircle from "../components/ScoreCircle";
import LoadingSpinner from "../components/LoadingSpinner";
import ErrorCard from "../components/ErrorCard";

interface IngredientInput {
  id: number;
  name: string;
  weight: string;
}

export default function FormulaAnalysis() {
  const [formulaName, setFormulaName] = useState("Demo Formula");
  const [ingredients, setIngredients] = useState<IngredientInput[]>([
    { id: 1, name: "Resveratrol", weight: "1.0" },
    { id: 2, name: "Quercetin", weight: "1.5" },
  ]);
  const [nextId, setNextId] = useState(3);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<FormulaAnalyzeResponse | null>(null);

  const formulaMaxScore = result
    ? result.component_scores.length * 60 + Math.min(2 * result.component_scores.length, 10)
    : 100;

  const handleAddIngredient = () => {
    setIngredients([...ingredients, { id: nextId, name: "", weight: "" }]);
    setNextId(nextId + 1);
  };

  const handleUpdateIngredient = (id: number, field: keyof IngredientInput, value: string) => {
    setIngredients(ingredients.map((item) => (item.id === id ? { ...item, [field]: value } : item)));
  };

  const handleRemoveIngredient = (id: number) => {
    setIngredients(ingredients.filter((item) => item.id !== id));
  };

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError(null);

    const validIngredients = ingredients
      .filter((item) => item.name.trim().length > 0)
      .map((item) => ({
        name: item.name.trim(),
        ...(item.weight.trim() ? { weight: Number(item.weight) } : {}),
      }));

    if (validIngredients.length === 0) {
      setError("请至少输入一个成分");
      setLoading(false);
      return;
    }

    try {
      const response = await analyzeFormula({
        formula_name: formulaName,
        ingredients: validIngredients,
      });

      if (!response.success || !response.data) {
        setResult(null);
        setError(response.error?.message ?? "分析失败");
        return;
      }

      setResult(response.data);
    } catch {
      setResult(null);
      setError("请求失败，请确认后端方剂分析接口可用");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="page-container">
      <h2 className="page-title">方剂分析</h2>
      <div className="grid-layout">
        
        {/* 左侧表单 */}
        <div className="card" style={{ alignSelf: "start" }}>
          <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "var(--space-md)" }}>
            <div>
              <label htmlFor="formula-name" className="label">方剂名称</label>
              <input
                id="formula-name"
                className="input"
                type="text"
                value={formulaName}
                onChange={(event) => setFormulaName(event.target.value)}
                placeholder="例如: 六味地黄丸"
                required
              />
            </div>

            <div>
              <label className="label">方剂成分</label>
              <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-sm)" }}>
                <AnimatePresence initial={false}>
                  {ingredients.map((item) => (
                    <motion.div
                      key={item.id}
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: "auto" }}
                      exit={{ opacity: 0, height: 0 }}
                      transition={{ duration: 0.2 }}
                      style={{ overflow: "hidden" }}
                    >
                      <div style={{ display: "flex", gap: "var(--space-sm)", alignItems: "center" }}>
                        <input
                          className="input"
                          type="text"
                          value={item.name}
                          onChange={(e) => handleUpdateIngredient(item.id, "name", e.target.value)}
                          placeholder="成分名称"
                          style={{ flex: 2 }}
                        />
                        <input
                          className="input"
                          type="number"
                          value={item.weight}
                          onChange={(e) => handleUpdateIngredient(item.id, "weight", e.target.value)}
                          placeholder="权重 (可选)"
                          step="0.1"
                          min="0"
                          style={{ flex: 1 }}
                        />
                        <button
                          type="button"
                          onClick={() => handleRemoveIngredient(item.id)}
                          style={{
                            color: "var(--color-text-secondary)",
                            padding: "8px",
                            cursor: "pointer",
                            transition: "color var(--transition-fast)",
                          }}
                          onMouseEnter={(e) => (e.currentTarget.style.color = "var(--color-error)")}
                          onMouseLeave={(e) => (e.currentTarget.style.color = "var(--color-text-secondary)")}
                        >
                          ✕
                        </button>
                      </div>
                    </motion.div>
                  ))}
                </AnimatePresence>
                
                <button
                  type="button"
                  onClick={handleAddIngredient}
                  style={{
                    padding: "var(--space-sm)",
                    borderRadius: "var(--radius-md)",
                    border: "2px dashed var(--color-border)",
                    color: "var(--color-primary)",
                    background: "transparent",
                    cursor: "pointer",
                    transition: "all var(--transition-fast)",
                    fontWeight: 500,
                    marginTop: "var(--space-xs)",
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.borderColor = "var(--color-primary)";
                    e.currentTarget.style.background = "var(--color-primary-light)";
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.borderColor = "var(--color-border)";
                    e.currentTarget.style.background = "transparent";
                  }}
                >
                  + 添加成分
                </button>
              </div>
            </div>

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
            <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} style={{ display: "flex", flexDirection: "column", gap: "var(--space-lg)" }}>
              
              {result.unresolved_ingredients.length > 0 && (
                <div style={{
                  background: "var(--color-warning)",
                  color: "#fff",
                  padding: "var(--space-md)",
                  borderRadius: "var(--radius-md)",
                  display: "flex",
                  alignItems: "center",
                  gap: "var(--space-sm)",
                  fontWeight: 500
                }}>
                  ⚠️ 有 {result.unresolved_ingredients.length} 个成分无法解析，可能会影响最终评分：
                  {result.unresolved_ingredients.join(", ")}
                </div>
              )}

              <div className="card" style={{ display: "flex", gap: "var(--space-xl)", alignItems: "center" }}>
                <ScoreCircle score={result.total_score} maxScore={formulaMaxScore} label="总体推荐分" />
                <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-md)" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: "var(--space-sm)" }}>
                    <span className="label" style={{ marginBottom: 0 }}>成分评分条目数：</span>
                    <span style={{ fontWeight: 600 }}>{result.component_scores.length}</span>
                  </div>
                  <div style={{ display: "flex", alignItems: "center", gap: "var(--space-sm)" }}>
                    <span className="label" style={{ marginBottom: 0 }}>协同加分：</span>
                    <span style={{ 
                      fontWeight: 600, 
                      color: "var(--color-primary-dark)", 
                      background: "var(--color-primary-light)",
                      padding: "2px 8px",
                      borderRadius: "var(--radius-full)"
                    }}>
                      +{result.synergy_bonus}
                    </span>
                  </div>
                  <p style={{ fontSize: "var(--text-sm)", color: "var(--color-text-secondary)", marginTop: "var(--space-sm)" }}>
                    基于各成分的基础属性以及它们在方剂中的组合协同效应综合计算得出。
                  </p>
                </div>
              </div>

              <div className="card">
                <h3 style={{ fontSize: "var(--text-lg)", marginBottom: "var(--space-md)", borderBottom: "1px solid var(--color-border)", paddingBottom: "var(--space-sm)" }}>成分明细</h3>
                <div style={{ overflowX: "auto" }}>
                  <table style={{ width: "100%", textAlign: "left", fontSize: "var(--text-sm)" }}>
                    <thead>
                      <tr style={{ color: "var(--color-text-secondary)", borderBottom: "1px solid var(--color-border)" }}>
                        <th style={{ padding: "8px" }}>成分名称</th>
                        <th style={{ padding: "8px" }}>解析状态</th>
                        <th style={{ padding: "8px" }}>单项评分</th>
                      </tr>
                    </thead>
                    <tbody>
                      {result.component_scores.map((item, idx) => (
                        <tr key={idx} style={{ 
                          borderBottom: "1px solid var(--color-border)",
                          background: item.resolved ? "transparent" : "rgba(249, 168, 37, 0.05)"
                        }}>
                          <td style={{ padding: "12px 8px", fontWeight: 500 }}>{item.ingredient_name}</td>
                          <td style={{ padding: "12px 8px" }}>
                            {item.resolved ? (
                              <span style={{ color: "var(--color-success)", fontWeight: 500 }}>✓ 已解析</span>
                            ) : (
                              <span style={{ color: "var(--color-warning)", fontWeight: 500 }}>✗ 未解析</span>
                            )}
                          </td>
                          <td style={{ padding: "12px 8px", fontWeight: 600 }}>{item.total_score}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

            </motion.div>
          )}
        </div>
      </div>
    </div>
  );
}
