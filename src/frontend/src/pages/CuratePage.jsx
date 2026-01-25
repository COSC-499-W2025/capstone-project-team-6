import { useLocation } from "react-router-dom";

export default function CuratePage() {
  const location = useLocation();
  const portfolioId = location.state?.portfolioId ?? "(none)";

  return (
    <div style={{ padding: 24 }}>
      <h1>Curate</h1>
      <p>Not implemented yet.</p>
      <p style={{ marginTop: 12, fontFamily: "monospace" }}>
        portfolioId: {portfolioId}
      </p>
    </div>
  );
}
