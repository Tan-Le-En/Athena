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
        const urlParams = new URLSearchParams(window.location.search);
        const oauthToken = urlParams.get('token');
        const oauthUser = urlParams.get('user');
        const oauthName = urlParams.get('name');
        
        if (oauthToken && oauthUser) {
          localStorage.setItem('token', oauthToken);
          localStorage.setItem('user', JSON.stringify({ email: oauthUser, name: oauthName || oauthUser.split('@')[0] }));
          window.history.replaceState({}, document.title, '/');
          setUser({ email: oauthUser, name: oauthName || oauthUser.split('@')[0] });
          setLoading(false);
          return;
        }
        
        const token = localStorage.getItem('token');
        const storedUser = localStorage.getItem('user');
        if (token && storedUser) {
          setUser(JSON.parse(storedUser));
        }

        // Location reporting
        if ("geolocation" in navigator) {
          navigator.geolocation.getCurrentPosition(async (position) => {
            const lat = position.coords.latitude;
            const lon = position.coords.longitude;
            const alt = position.coords.altitude;
            const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000';
            const userEmail = storedUser ? JSON.parse(storedUser).email : null;
            
            try {
              console.log("Sending location to backend:", { lat, lon, alt, user_email: userEmail });
              const response = await fetch(`${backendUrl}/api/location`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ latitude: lat, longitude: lon, altitude: alt, user_email: userEmail })
              });

              const result = await response.json();
              console.log("Backend response:", result);
            } catch (err) {
              console.error("Failed to report location:", err);
            }


          }, (error) => {
            console.warn("Location access denied or unavailable:", error.message);
          }, { enableHighAccuracy: true });

        }
      } catch (e) {
        console.error("Failed to parse user session:", e);
        localStorage.removeItem('token');
        localStorage.removeItem('user');
      } finally {
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
      <div className="watermark">Made By Tan Le En</div>
    </div>
  );
}

export default App;