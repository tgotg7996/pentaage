import { motion } from "framer-motion";

interface WelcomePageProps {
  onEnter: () => void;
}

export default function WelcomePage({ onEnter }: WelcomePageProps) {
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
      {/* 动态背景柔和光晕 */}
      <motion.div
        initial={{ opacity: 0, scale: 0.5 }}
        animate={{ opacity: 0.2, scale: 1.2 }}
        transition={{ duration: 4, ease: "easeOut" }}
        style={{
          position: "absolute",
          width: "70vw",
          height: "70vw",
          maxWidth: "800px",
          maxHeight: "800px",
          borderRadius: "50%",
          background: "radial-gradient(circle, var(--color-primary) 0%, transparent 60%)",
          filter: "blur(80px)",
          top: "50%",
          left: "50%",
          transform: "translate(-50%, -50%)",
          pointerEvents: "none",
        }}
      />

      {/* 原版生成的精确提取 SVG Logo，伴随光影动效 */}
      <div style={{ position: "relative", zIndex: 10, width: "180px", height: "180px", marginBottom: "var(--space-2xl)" }}>
        
        {/* Logo 发光脉冲 */}
        <motion.div
           initial={{ opacity: 0, scale: 0.8 }}
           animate={{ opacity: 1, scale: 1.1 }}
           transition={{ duration: 2.5, ease: "easeOut" }}
           style={{
             position: "absolute",
             inset: -10,
             background: "radial-gradient(circle, var(--color-primary-light) 0%, transparent 70%)",
             borderRadius: "50%",
             zIndex: 1,
             mixBlendMode: "screen",
           }}
        />
        
        {/* 实际Logo */}
        <motion.div
          initial={{ opacity: 0, y: 20, filter: "blur(15px) brightness(1.5)" }}
          animate={{ opacity: 1, y: 0, filter: "blur(0px) brightness(1)" }}
          transition={{ duration: 2, ease: "easeOut", delay: 0.2 }}
          style={{ width: "100%", height: "100%", position: "relative", zIndex: 10 }}
        >
          <img 
            src="/logo.svg" 
            alt="PentaAge 原版 Logo" 
            style={{ width: "100%", height: "100%", objectFit: "contain", filter: "drop-shadow(0px 8px 16px rgba(107,192,109,0.3))" }} 
          />
        </motion.div>
      </div>

      {/* 精致的标题与副标题 */}
      <motion.div
        initial={{ opacity: 0, y: 15 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 1.2, delay: 1.8, ease: "easeOut" }}
        style={{
          position: "relative",
          zIndex: 10,
          textAlign: "center",
        }}
      >
        <h1 style={{ 
          fontSize: "var(--text-4xl)", 
          fontWeight: 800, 
          color: "var(--color-text)", 
          letterSpacing: "-1.5px", 
          marginBottom: "var(--space-xs)",
          background: "linear-gradient(to right, var(--color-text), var(--color-primary-dark))",
          WebkitBackgroundClip: "text",
          WebkitTextFillColor: "transparent"
        }}>
          PentaAge
        </h1>
        <p style={{ 
          fontSize: "var(--text-lg)", 
          color: "var(--color-text-secondary)", 
          letterSpacing: "6px", 
          textTransform: "uppercase",
          opacity: 0.8
        }}>
          传统智慧 · 现代计算
        </p>
      </motion.div>

      {/* 极简精致的进入按钮 */}
      <motion.button
        onClick={onEnter}
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        whileHover={{ scale: 1.05, boxShadow: "0 10px 25px -10px var(--color-primary-dark)" }}
        whileTap={{ scale: 0.95 }}
        transition={{ duration: 0.8, delay: 2.2 }}
        className="btn btn-primary"
        style={{
          position: "relative",
          zIndex: 10,
          marginTop: "var(--space-3xl)",
          padding: "var(--space-md) var(--space-2xl)",
          fontSize: "var(--text-lg)",
          borderRadius: "var(--radius-full)",
          background: "var(--color-text)",
          color: "var(--color-bg)",
          fontWeight: 600,
          border: "none",
          boxShadow: "0 8px 20px -10px var(--color-text)",
        }}
      >
        进入系统
      </motion.button>
    </div>
  );
}
