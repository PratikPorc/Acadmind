import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { FacultyApp } from "./pages/FacultyApp";
import { LandingPage } from "./pages/LandingPage";
import { StudentApp } from "./pages/StudentApp";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/faculty/*" element={<FacultyApp />} />
        <Route path="/student/*" element={<StudentApp />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
