import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom"
import LookupPage from "@/pages/LookupPage"
import TrackPage from "@/pages/TrackPage"

export default function App() {
  return (
    <BrowserRouter basename="/EasyPC">
      <Routes>
        <Route path="/" element={<LookupPage />} />
        <Route path="/track/:wo/:token" element={<TrackPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
