import { Routes, Route } from 'react-router-dom'
import Home from './pages/Home'
import GetStarted from './pages/GetStarted'
import Analyzing from './pages/Analyzing'
import Dashboard from './pages/Dashboard'

function App() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/get-started" element={<GetStarted />} />
      <Route path="/analyzing" element={<Analyzing />} />
      <Route path="/dashboard" element={<Dashboard />} />
    </Routes>
  )
}

export default App
