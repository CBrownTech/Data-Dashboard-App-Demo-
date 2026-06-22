// Apply saved theme before React renders to avoid a flash of the wrong theme
if (localStorage.getItem('theme') === 'dark') {
  document.documentElement.classList.add('dark')
}

import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { Provider } from 'react-redux'
import { store } from './store'
import './index.css'
import App from './App.tsx'

/* Provider wraps the entire app so every component can access the Redux store
   via useSelector (read state) and useDispatch (trigger actions). */
createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <Provider store={store}>
      <App />
    </Provider>
  </StrictMode>,
)
