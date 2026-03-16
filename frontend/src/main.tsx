import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import "./styles/reset.css";
import "./styles/variables.css";
import "./styles/global.css";
import "./styles/animations.css";
import "./styles/welcome.css";
import "./styles/navbar.css";

import App from "./App";

const rootElement = document.getElementById("root");

if (!rootElement) {
  throw new Error("Root element not found");
}

createRoot(rootElement).render(
  <StrictMode>
    <App />
  </StrictMode>
);
