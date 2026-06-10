import { Routes, Route } from "react-router-dom";
import Layout from "./components/Layout";
import Dashboard from "./pages/Dashboard";
import NewAssessment from "./pages/NewAssessment";
import RiskReport from "./pages/RiskReport";
import ModelInsights from "./pages/ModelInsights";

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<Dashboard />} />
        <Route path="/assess" element={<NewAssessment />} />
        <Route path="/report" element={<RiskReport />} />
        <Route path="/model" element={<ModelInsights />} />
      </Route>
    </Routes>
  );
}
