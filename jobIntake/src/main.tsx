import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import './index.css'
import App from './App.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <BrowserRouter>
      <App />
      <Toaster
        position="top-right"
        toastOptions={{
          duration: 2400,
          icon: null,
          style: {
            fontSize: '14px',
            background: '#f8fafc',
            color: '#0f172a',
            border: '1px solid #e2e8f0',
          },
          success: {
            style: {
              background: '#dcfce7',
              color: '#166534',
              border: '1px solid #86efac',
            },
          },
          error: {
            style: {
              background: '#fee2e2',
              color: '#991b1b',
              border: '1px solid #fca5a5',
            },
          },
        }}
      />
    </BrowserRouter>
  </StrictMode>,
)
