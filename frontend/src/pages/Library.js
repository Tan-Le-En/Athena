import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { BookOpen, Library as LibraryIcon, LogOut, User, ArrowLeft } from 'lucide-react';
import axios from 'axios';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function Library({ user, logout }) {
  const [library, setLibrary] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    loadLibrary();
  }, []);

  const loadLibrary = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/library`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setLibrary(response.data);
    } catch (error) {
      toast.error('Failed to load library');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-canvas">
      <header className="border-b-2 border-ink bg-paper sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Button
              variant="ghost"
              onClick={() => navigate('/')}
              className="rounded-none"
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back
            </Button>
            <LibraryIcon className="w-8 h-8 text-signal" strokeWidth={2.5} />
            <h1 className="text-2xl font-heading font-bold text-ink tracking-tight">My Library</h1>
          </div>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2 px-3 py-2 bg-warmgrey rounded-none">
              <User className="w-4 h-4" />
              <span className="text-sm font-medium">{user.name}</span>
            </div>
            <Button onClick={logout} variant="ghost" className="rounded-none">
              <LogOut className="w-4 h-4" />
            </Button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-12">
        {loading ? (
          <div className="text-center py-12">
            <div className="text-ink text-xl font-heading">Loading library...</div>
          </div>
        ) : library.length === 0 ? (
          <div className="text-center py-20">
            <LibraryIcon className="w-16 h-16 text-concrete mx-auto mb-4" />
            <h2 className="text-2xl font-heading font-bold text-ink mb-2">Your library is empty</h2>
            <p className="text-concrete mb-6">Start reading books to build your collection</p>
            <Button
              onClick={() => navigate('/')}
              className="bg-signal text-white hover:bg-[#B02015] rounded-none font-bold tracking-wide uppercase"
            >
              Search Books
            </Button>
          </div>
        ) : (
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {library.map((item, idx) => (
              <div
                key={idx}
                onClick={() => navigate(`/reader/${item.book.isbn}`)}
                className="bg-paper border-2 border-ink p-4 cursor-pointer constructivist-border"
                data-testid={`library-book-${idx}`}
              >
                <div className="flex gap-4">
                  {item.book.cover_url ? (
                    <img
                      src={item.book.cover_url}
                      alt={item.book.title}
                      className="w-20 h-28 object-cover border-2 border-ink"
                    />
                  ) : (
                    <div className="w-20 h-28 bg-warmgrey border-2 border-ink flex items-center justify-center">
                      <BookOpen className="w-8 h-8 text-concrete" />
                    </div>
                  )}
                  <div className="flex-1">
                    <h3 className="font-heading font-bold text-ink mb-1">{item.book.title}</h3>
                    <p className="text-sm text-concrete mb-2">{item.book.authors.join(', ')}</p>
                    <div className="mt-4">
                      <div className="flex items-center justify-between text-xs mb-1">
                        <span className="text-concrete">Progress</span>
                        <span className="font-medium text-ink">{item.progress.toFixed(0)}%</span>
                      </div>
                      <div className="h-2 bg-warmgrey border border-ink">
                        <div
                          className="h-full bg-signal"
                          style={{ width: `${item.progress}%` }}
                        />
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}