import { Navigate, Route, Routes } from "react-router-dom";
import { Layout } from "./components/Layout";
import { BatteryHealth } from "./pages/BatteryHealth";
import { Charges } from "./pages/Charges";
import { Controls } from "./pages/Controls";
import { Diagnostics } from "./pages/Diagnostics";
import { Live } from "./pages/Live";
import { Overview } from "./pages/Overview";
import { Rides } from "./pages/Rides";
import { SessionDetail } from "./pages/SessionDetail";

export default function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Overview />} />
        <Route path="/rides" element={<Rides />} />
        <Route path="/rides/:id" element={<SessionDetail type="ride" />} />
        <Route path="/charges" element={<Charges />} />
        <Route path="/charges/:id" element={<SessionDetail type="charge" />} />
        <Route path="/battery" element={<BatteryHealth />} />
        <Route path="/live" element={<Live />} />
        <Route path="/diagnostics" element={<Diagnostics />} />
        <Route path="/controls" element={<Controls />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Layout>
  );
}
