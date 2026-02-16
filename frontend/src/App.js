import "@/App.css";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { useState, useEffect } from "react";
import Home from "./pages/Home";
import Auth from "./pages/Auth";
import Reader from "./pages/Reader";
import Library from "./pages/Library";
import { Toaster } from "@/components/ui/sonner";

function App() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const initializeApp = async () => {
      try {
        const token = localStorage.getItem('token');
        const storedUser = localStorage.getItem('user');
        if (token && storedUser) {
          setUser(JSON.parse(storedUser));
        }
      } catch (e) {
        console.error("Failed to parse user session:", e);
        localStorage.removeItem('token');
        localStorage.removeItem('user');
      } finally {
        // Shorter delay for "fast" feel while still showing the brand
        setTimeout(() => setLoading(false), 800);
      }
    };
    initializeApp();
  }, []);

  const login = (token, userData) => {
    localStorage.setItem('token', token);
    localStorage.setItem('user', JSON.stringify(userData));
    setUser(userData);
  };

  const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setUser(null);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-canvas">
        <div className="relative">
          <div className="text-ink text-3xl font-serif italic animate-pulse tracking-tighter">Athena</div>
          <div className="h-px bg-ink w-full mt-2 origin-left scale-x-0 animate-in fade-in slide-in-from-left duration-1000 fill-mode-forwards" />
        </div>
      </div>
    );
  }

  return (
    <div className="App">
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Home user={user} logout={logout} />} />
          <Route 
            path="/auth" 
            element={user ? <Navigate to="/" /> : <Auth onLogin={login} />} 
          />
          <Route 
            path="/reader/:isbn" 
            element={user ? <Reader user={user} logout={logout} /> : <Navigate to="/auth" />} 
          />
          <Route 
            path="/library" 
            element={user ? <Library user={user} logout={logout} /> : <Navigate to="/auth" />} 
          />
        </Routes>
      </BrowserRouter>
      <Toaster position="top-right" />
      <div className="watermark">Tan Le En</div>
    </div>
  );
}

export default App;