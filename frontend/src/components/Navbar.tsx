import ThemeToggle from "./ThemeToggle";
import HealthIndicator from "./HealthIndicator";
import "../styles/navbar.css";

type PageKey = "compound" | "formula" | "batch";

interface NavbarProps {
  currentPage: PageKey;
  onPageChange: (page: PageKey) => void;
  themeMode: "system" | "light" | "dark";
  onThemeToggle: () => void;
}

const tabs: { key: PageKey; label: string }[] = [
  { key: "compound", label: "单体分析" },
  { key: "formula", label: "方剂分析" },
  { key: "batch", label: "批量任务" },
];

export default function Navbar({ currentPage, onPageChange, themeMode, onThemeToggle }: NavbarProps) {
  return (
    <nav className="navbar">
      <div className="navbar-brand">
        <img src="/logo.png" alt="PentaAge" />
        <span>PentaAge</span>
      </div>
      <div className="navbar-tabs">
        {tabs.map((tab) => (
          <button
            key={tab.key}
            type="button"
            className={`navbar-tab ${currentPage === tab.key ? "active" : ""}`}
            onClick={() => onPageChange(tab.key)}
          >
            {tab.label}
          </button>
        ))}
      </div>
      <div className="navbar-actions">
        <HealthIndicator />
        <ThemeToggle mode={themeMode} onToggle={onThemeToggle} />
      </div>
    </nav>
  );
}
