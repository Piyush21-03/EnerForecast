import { createContext, useContext, useState } from "react";

const AuthContext = createContext();

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    try {
      if (typeof window !== "undefined" && window.localStorage) {
        const saved = window.localStorage.getItem("energyfc_user");
        if (saved) return JSON.parse(saved);
      }
    } catch {
      // fallback
    }
    return null;
  });

  const login = (email, password) => {
    const rawName = email.split("@")[0].replace(/[._]/g, " ");
    const formattedName =
      rawName
        .split(" ")
        .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
        .join(" ") || "Energy Specialist";

    const newUser = {
      name: formattedName,
      email: email || "operator@energyfc.ai",
      role: "Inference Specialist",
      avatar: "⚡",
    };

    setUser(newUser);
    try {
      if (typeof window !== "undefined" && window.localStorage) {
        window.localStorage.setItem("energyfc_user", JSON.stringify(newUser));
      }
    } catch {
      // ignore
    }
    return true;
  };

  const logout = () => {
    setUser(null);
    try {
      if (typeof window !== "undefined" && window.localStorage) {
        window.localStorage.removeItem("energyfc_user");
      }
    } catch {
      // ignore
    }
  };

  return (
    <AuthContext.Provider value={{ user, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    return {
      user: { name: "Piyush Panigrahi", email: "piyush@energyfc.ai", role: "Analyst" },
      login: () => true,
      logout: () => {},
    };
  }
  return ctx;
}
