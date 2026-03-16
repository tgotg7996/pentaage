import { useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { useTheme } from "./hooks/useTheme";
import Navbar from "./components/Navbar";
import WelcomePage from "./pages/WelcomePage";

import BatchTask from "./pages/BatchTask";
import CompoundAnalysis from "./pages/CompoundAnalysis";
import FormulaAnalysis from "./pages/FormulaAnalysis";

type PageKey = "compound" | "formula" | "batch";

const pageOrder: PageKey[] = ["compound", "formula", "batch"];

export default function App() {
  const [showWelcome, setShowWelcome] = useState(true);
  const [page, setPage] = useState<PageKey>("compound");
  const [prevPage, setPrevPage] = useState<PageKey>("compound");
  const { mode, toggleTheme } = useTheme();

  if (showWelcome) {
    return <WelcomePage onEnter={() => setShowWelcome(false)} />;
  }

  const direction = pageOrder.indexOf(page) >= pageOrder.indexOf(prevPage) ? 1 : -1;

  const handlePageChange = (newPage: PageKey) => {
    setPrevPage(page);
    setPage(newPage);
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 30 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, ease: "easeOut" }}
    >
      <Navbar
        currentPage={page}
        onPageChange={handlePageChange}
        themeMode={mode}
        onThemeToggle={toggleTheme}
      />
      <div className="main-content">
        <AnimatePresence mode="wait">
          <motion.div
            key={page}
            initial={{ opacity: 0, x: 60 * direction }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -60 * direction }}
            transition={{ duration: 0.3, ease: "easeInOut" }}
          >
            {page === "compound" && <CompoundAnalysis />}
            {page === "formula" && <FormulaAnalysis />}
            {page === "batch" && <BatchTask />}
          </motion.div>
        </AnimatePresence>
      </div>
    </motion.div>
  );
}
