import { useState } from "react";

import BatchTask from "./pages/BatchTask";
import CompoundAnalysis from "./pages/CompoundAnalysis";
import FormulaAnalysis from "./pages/FormulaAnalysis";

type PageKey = "compound" | "formula" | "batch";

export default function App() {
  const [page, setPage] = useState<PageKey>("compound");

  return (
    <main style={{ fontFamily: "sans-serif", padding: "24px" }}>
      <h1>PentaAge</h1>
      <div style={{ display: "flex", gap: "8px", marginBottom: "16px" }}>
        <button onClick={() => setPage("compound")} type="button">
          单体分析
        </button>
        <button onClick={() => setPage("formula")} type="button">
          方子分析
        </button>
        <button onClick={() => setPage("batch")} type="button">
          批量任务
        </button>
      </div>
      {page === "compound" && <CompoundAnalysis />}
      {page === "formula" && <FormulaAnalysis />}
      {page === "batch" && <BatchTask />}
    </main>
  );
}
