import { createContext, useContext, useEffect, useState } from "react";

const ThemeContext = createContext();

export function ThemeProvider({ children }) {
  const [theme, setTheme] = useState(() => {
    try {
      if (typeof window !== "undefined" && window.localStorage && typeof window.localStorage.getItem === "function") {
        return window.localStorage.getItem("energyfc_theme") || "dark";
      }
    } catch {
      // ignore
    }
    return "dark";
  });

  useEffect(() => {
    try {
      if (typeof document !== "undefined") {
        document.documentElement.setAttribute("data-theme", theme);
      }
      if (typeof window !== "undefined" && window.localStorage && typeof window.localStorage.setItem === "function") {
        window.localStorage.setItem("energyfc_theme", theme);
      }
    } catch {
      // ignore
    }
  }, [theme]);

  const toggleTheme = () => {
    setTheme((prev) => (prev === "dark" ? "light" : "dark"));
  };

  return (
    <ThemeContext.Provider value={{ theme, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const ctx = useContext(ThemeContext);
  if (!ctx) {
    return { theme: "dark", toggleTheme: () => {} };
  }
  return ctx;
}
