import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom' 
import './index.css'
import App from './App.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <BrowserRouter> {/* 브라우저가 경로를 인식할 수 있게 감싸줍니다 */}
      <App />
    </BrowserRouter>
  </StrictMode>,
)