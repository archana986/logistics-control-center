import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import IncidentResponseView from './pages/IncidentResponseView'
import './app.css'

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Navigate to="/incident-response" replace />} />
        <Route path="/incident-response" element={<IncidentResponseView />} />
      </Routes>
    </Router>
  )
}

export default App
