import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './index.css'
import { BrowserRouter } from "react-router-dom";
import { DataContextProvider } from './context/ContextProvider.jsx';
ReactDOM.createRoot(document.getElementById('root')).render(
    <BrowserRouter>
      <DataContextProvider>
        <App />
      </DataContextProvider>
    </BrowserRouter>
  ,
)
