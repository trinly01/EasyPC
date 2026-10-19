import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom"
import LookupPage from "@/pages/LookupPage"
import TrackPage from "@/pages/TrackPage"
import BookPage from "@/pages/BookPage"
import ManageBookingPage from "@/pages/ManageBookingPage"

export default function App() {
  return (
    <BrowserRouter basename="/EasyPC">
      <Routes>
        <Route path="/" element={<LookupPage />} />
        <Route path="/track/:wo/:key" element={<TrackPage />} />
        <Route path="/book" element={<BookPage />} />
        <Route path="/book/manage" element={<ManageBookingPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
