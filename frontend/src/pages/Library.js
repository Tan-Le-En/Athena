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
    <div className="min-h-screen bg-canvas font-sans">
      <header className="border-b border-border bg-paper/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-6">
            <Button
              variant="ghost"
              onClick={() => navigate('/')}
              className="rounded-none hover:bg-transparent hover:text-ink/70 px-0"
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              <span className="font-sans uppercase tracking-widest text-xs font-bold">Return</span>
            </Button>
            <div className="h-6 w-px bg-border"></div>
            <h1 className="text-xl font-serif font-bold text-ink italic">Athena Collection</h1>
          </div>
          <div className="flex items-center gap-6">
             <div className="hidden md:flex items-center gap-2">
                <span className="text-[10px] uppercase tracking-widest text-muted-foreground font-bold">Reader</span>
                <span className="font-serif italic text-lg">{user.name}</span>
             </div>
            <Button onClick={logout} variant="ghost" className="rounded-none hover:bg-destructive hover:text-white transition-colors">
              <LogOut className="w-4 h-4" />
            </Button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-16">
        <div className="mb-12 border-b border-ink/10 pb-8">
            <h2 className="text-6xl font-serif font-black mb-4">Your Archive</h2>
            <p className="font-sans text-muted-foreground max-w-xl leading-relaxed">
                A curated selection of literary works you are currently verifying and consuming.
            </p>
        </div>

        {loading ? (
          <div className="text-center py-24">
             <div className="text-ink text-xl font-serif italic animate-pulse">Retrieving archives...</div>
          </div>
        ) : library.length === 0 ? (
          <div className="text-center py-32 border border-dashed border-border">
            <LibraryIcon className="w-12 h-12 text-muted-foreground mx-auto mb-6 opacity-50" />
            <h2 className="text-3xl font-serif font-bold text-ink mb-3">The shelves are empty</h2>
            <p className="text-muted-foreground mb-8 font-sans">Begin your collection by adding a verified work.</p>
            <Button
              onClick={() => navigate('/')}
              className="bg-ink text-paper hover:bg-ink/90 rounded-none font-sans font-bold tracking-widest uppercase px-8 py-6"
            >
              Discover Works
            </Button>
          </div>
        ) : (
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-x-8 gap-y-16">
            {library.map((item, idx) => (
              <div
                key={idx}
                onClick={() => navigate(`/reader/${item.book.isbn}`)}
                className="group cursor-pointer"
                data-testid={`library-book-${idx}`}
              >
                <div className="relative aspect-[2/3] mb-6 overflow-hidden bg-warmgrey border border-ink/10 group-hover:border-ink transition-colors">
                  {item.book.cover_url ? (
                    <img
                      src={item.book.cover_url}
                      alt={item.book.title}
                      className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-105"
                    />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center bg-paper">
                      <BookOpen className="w-12 h-12 text-muted-foreground/30" />
                    </div>
                  )}
                  <div className="absolute inset-0 bg-ink/0 group-hover:bg-ink/5 transition-colors" />
                  
                  <div className="absolute bottom-0 left-0 right-0 bg-paper border-t border-ink px-4 py-3 flex justify-between items-center transform translate-y-full group-hover:translate-y-0 transition-transform duration-300">
                     <span className="font-sans text-[10px] uppercase tracking-widest font-bold">Continue</span>
                     <span className="font-serif italic">{item.progress.toFixed(0)}%</span>
                  </div>
                </div>

                <div className="space-y-2">
                    <div className="flex justify-between items-start border-t border-ink pt-3">
                        <span className="font-sans text-[10px] uppercase tracking-widest text-muted-foreground font-bold">No. {idx + 1}</span>
                         <span className="font-sans text-[10px] uppercase tracking-widest text-muted-foreground font-bold">{item.last_read ? new Date(item.last_read).toLocaleDateString() : 'New'}</span>
                    </div>
                    <h3 className="font-serif text-2xl font-bold leading-tight group-hover:underline decoration-1 underline-offset-4">{item.book.title}</h3>
                    <p className="font-serif italic text-muted-foreground">{item.book.authors?.join(', ') || 'Unknown Author'}</p>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}