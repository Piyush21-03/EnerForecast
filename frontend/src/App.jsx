import { Route, Routes } from "react-router-dom";

import MainLayout from "./layouts/MainLayout.jsx";
import About from "./pages/About.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import Forecast from "./pages/Forecast.jsx";
import History from "./pages/History.jsx";
import Model from "./pages/Model.jsx";

export default function App() {
  return (
    <Routes>
      <Route element={<MainLayout />}>
        <Route index element={<Dashboard />} />
        <Route path="forecast" element={<Forecast />} />
        <Route path="history" element={<History />} />
        <Route path="model" element={<Model />} />
        <Route path="about" element={<About />} />
        <Route path="*" element={<Dashboard />} />
      </Route>
    </Routes>
  );
}
