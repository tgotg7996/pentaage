import { motion } from "framer-motion";

interface WelcomePageProps {
  onEnter: () => void;
}

export default function WelcomePage({ onEnter }: WelcomePageProps) {
  // SVG 动画的路径设定（简化版的叶子叠加五边形）
  const pentagonPath = "M 50 5 L 95 38 L 78 90 L 22 90 L 5 38 Z";
  const leafPath = "M 50 5 C 60 -10 80 -10 90 0 C 100 10 100 30 85 40 C 70 50 55 25 50 5 Z M 50 5 C 40 -10 20 -10 10 0 C 0 10 0 30 15 40 C 30 50 45 25 50 5 Z";

  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        background: "var(--color-bg)",
        zIndex: 1000,
        overflow: "hidden",
      }}
    >
      {/* 动态背景光晕 */}
      <motion.div
        initial={{ opacity: 0, scale: 0.5 }}
        animate={{ opacity: 0.15, scale: 1.2 }}
        transition={{ duration: 4, ease: "easeOut" }}
        style={{
          position: "absolute",
          width: "60vw",
          height: "60vw",
          borderRadius: "50%",
          background: "radial-gradient(circle, var(--color-primary) 0%, transparent 70%)",
          filter: "blur(60px)",
          top: "50%",
          left: "50%",
          transform: "translate(-50%, -50%)",
          pointerEvents: "none",
        }}
      />

      {/* SVG 线条描边动画 Logo */}
      <motion.div
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ duration: 1, ease: "easeOut" }}
        style={{ position: "relative", zIndex: 10, width: "160px", height: "160px", marginBottom: "var(--space-2xl)" }}
      >
        <svg viewBox="0 -15 100 120" style={{ width: "100%", height: "100%", overflow: "visible" }}>
          {/* 五边形 */}
          <motion.path
            d={pentagonPath}
            fill="none"
            stroke="var(--color-primary)"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            initial={{ pathLength: 0, opacity: 0 }}
            animate={{ pathLength: 1, opacity: 1 }}
            transition={{ duration: 2, ease: "easeInOut", delay: 0.2 }}
          />
          {/* 绿叶 */}
          <motion.path
            d={leafPath}
            fill="none"
            stroke="var(--color-accent)"
            strokeWidth="3"
            strokeLinecap="round"
            strokeLinejoin="round"
            initial={{ pathLength: 0, opacity: 0 }}
            animate={{ pathLength: 1, opacity: 1 }}
            transition={{ duration: 2, ease: "easeInOut", delay: 1.2 }}
          />
          
          {/* 填充发光 */}
          <motion.path
            d={pentagonPath}
            fill="var(--color-primary)"
            style={{ mixBlendMode: "multiply" }}
            initial={{ opacity: 0 }}
            animate={{ opacity: 0.1 }}
            transition={{ duration: 2, delay: 2 }}
          />
          <motion.path
            d={leafPath}
            fill="var(--color-primary-dark)"
            style={{ mixBlendMode: "multiply" }}
            initial={{ opacity: 0 }}
            animate={{ opacity: 0.2 }}
            transition={{ duration: 2, delay: 2.5 }}
          />
        </svg>
      </motion.div>

      {/* 品牌文字 */}
      <motion.div
        initial={{ opacity: 0, y: 15 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 1.2, delay: 2.5, ease: "easeOut" }}
        style={{
          position: "relative",
          zIndex: 10,
          textAlign: "center",
        }}
      >
        <h1 style={{ fontSize: "var(--text-4xl)", fontWeight: 800, color: "var(--color-text)", letterSpacing: "-1px", marginBottom: "var(--space-xs)" }}>
          PentaAge
        </h1>
        <p style={{ fontSize: "var(--text-lg)", color: "var(--color-text-secondary)", letterSpacing: "4px", textTransform: "uppercase" }}>
          传统智慧 · 现代计算
        </p>
      </motion.div>

      {/* 进入按钮 */}
      <motion.button
        onClick={onEnter}
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        transition={{ duration: 0.8, delay: 3.2 }}
        className="btn btn-primary"
        style={{
          position: "relative",
          zIndex: 10,
          marginTop: "var(--space-3xl)",
          padding: "var(--space-md) var(--space-2xl)",
          fontSize: "var(--text-lg)",
          borderRadius: "var(--radius-full)",
          boxShadow: "0 10px 30px -10px var(--color-primary)",
        }}
      >
        开始使用
      </motion.button>
    </div>
  );
}
