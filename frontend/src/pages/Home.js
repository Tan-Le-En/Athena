import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, BookOpen, Library, LogOut, User } from 'lucide-react';
import axios from 'axios';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/components/ui/dialog';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function Home({ user, logout }) {
  const [isbn, setIsbn] = useState('');
  const [loading, setLoading] = useState(false);
  const [bookData, setBookData] = useState(null);
  const [showConfirmation, setShowConfirmation] = useState(false);
  const navigate = useNavigate();

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!isbn.trim()) {
      toast.error('Please enter an ISBN');
      return;
    }

    setLoading(true);
    try {
      const response = await axios.get(`${API}/books/search/${isbn}`);
      setBookData(response.data);
      setShowConfirmation(true);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to find book. Please check the ISBN.');
    } finally {
      setLoading(false);
    }
  };

  const handleReadNow = () => {
    if (!user) {
      toast.error('Please login to read books');
      navigate('/auth');
      return;
    }
    navigate(`/reader/${bookData.isbn}`);
  };

  return (
    <div className="min-h-screen bg-canvas relative overflow-hidden">
      <div className="geometric-shape w-96 h-96 bg-signal opacity-5 rounded-full absolute -top-48 -right-48" />
      <div className="geometric-shape w-64 h-64 bg-ink opacity-5 absolute bottom-0 -left-32" 
           style={{ clipPath: 'polygon(50% 0%, 0% 100%, 100% 100%)' }} />

      <header className="border-b-2 border-ink bg-paper/50 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <BookOpen className="w-8 h-8 text-signal" strokeWidth={2.5} />
            <h1 className="text-2xl font-heading font-bold text-ink tracking-tight">ATHENAVISION</h1>
          </div>
          <div className="flex items-center gap-4">
            {user ? (
              <>
                <Button
                  variant="ghost"
                  onClick={() => navigate('/library')}
                  className="rounded-none font-medium tracking-wide"
                  data-testid="library-nav-button"
                >
                  <Library className="w-4 h-4 mr-2" />
                  Library
                </Button>
                <div className="flex items-center gap-2 px-3 py-2 bg-warmgrey rounded-none">
                  <User className="w-4 h-4" />
                  <span className="text-sm font-medium">{user.name}</span>
                </div>
                <Button
                  onClick={logout}
                  variant="ghost"
                  className="rounded-none"
                  data-testid="logout-button"
                >
                  <LogOut className="w-4 h-4" />
                </Button>
              </>
            ) : (
              <Button
                onClick={() => navigate('/auth')}
                className="bg-signal text-white hover:bg-[#B02015] rounded-none font-bold tracking-wide uppercase h-10 px-6"
                data-testid="login-nav-button"
              >
                Login
              </Button>
            )}
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-20">
        <div className="grid lg:grid-cols-2 gap-12 items-center">
          <div className="space-y-8">
            <div className="space-y-4">
              <h2 className="text-5xl lg:text-6xl font-heading font-bold text-ink leading-tight text-balance">
                From ISBN to
                <span className="block text-signal">Instant Reading</span>
              </h2>
              <p className="text-lg text-concrete leading-relaxed">
                Have a book identifier? Get the full text in under 2 seconds. No apps, no friction—just pure literary access.
              </p>
            </div>

            <form onSubmit={handleSearch} className="space-y-4">
              <div className="relative">
                <Input
                  type="text"
                  placeholder="Enter ISBN (e.g., 9780141439518)"
                  value={isbn}
                  onChange={(e) => setIsbn(e.target.value)}
                  className="h-16 text-xl border-2 border-ink rounded-none bg-paper focus:border-signal isbn-input font-medium"
                  data-testid="isbn-search-input"
                />
                <Search className="absolute right-4 top-1/2 -translate-y-1/2 text-concrete w-6 h-6" />
              </div>
              <Button
                type="submit"
                disabled={loading}
                className="w-full h-14 bg-signal text-white hover:bg-[#B02015] rounded-none font-bold text-lg tracking-wide uppercase constructivist-border border-signal"
                data-testid="search-button"
              >
                {loading ? 'Searching...' : 'Search Book'}
              </Button>
            </form>

            <div className="grid grid-cols-3 gap-4 pt-8 border-t-2 border-warmgrey">
              <div className="text-center">
                <div className="text-3xl font-heading font-bold text-signal">{'<'}2s</div>
                <div className="text-sm text-concrete mt-1">Search Speed</div>
              </div>
              <div className="text-center">
                <div className="text-3xl font-heading font-bold text-signal">1000s</div>
                <div className="text-sm text-concrete mt-1">Books Available</div>
              </div>
              <div className="text-center">
                <div className="text-3xl font-heading font-bold text-signal">Free</div>
                <div className="text-sm text-concrete mt-1">Public Domain</div>
              </div>
            </div>
          </div>

          <div className="relative hidden lg:block">
            <div className="aspect-square bg-paper border-2 border-ink p-8 relative overflow-hidden">
              <img
                src="https://images.unsplash.com/photo-1597920940566-a77511f9327d?crop=entropy&cs=srgb&fm=jpg&q=85"
                alt="Library"
                className="w-full h-full object-cover"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-canvas/90 to-transparent" />
              <div className="absolute bottom-8 left-8 right-8">
                <p className="text-ink font-heading text-2xl font-bold">
                  "The only thing you absolutely have to know is the location of the library."
                </p>
                <p className="text-concrete mt-2">— Albert Einstein</p>
              </div>
            </div>
            <div className="absolute -bottom-6 -right-6 w-32 h-32 bg-signal opacity-20 rounded-none" />
          </div>
        </div>
      </main>

      <Dialog open={showConfirmation} onOpenChange={setShowConfirmation}>
        <DialogContent className="rounded-none border-2 border-ink bg-paper max-w-2xl">
          <DialogHeader>
            <DialogTitle className="text-2xl font-heading font-bold text-ink">Book Found</DialogTitle>
            <DialogDescription className="text-concrete">
              Confirm this is the book you're looking for
            </DialogDescription>
          </DialogHeader>
          {bookData && (
            <div className="flex gap-6 py-4">
              {bookData.cover_url ? (
                <img
                  src={bookData.cover_url}
                  alt={bookData.title}
                  className="w-32 h-48 object-cover border-2 border-ink"
                />
              ) : (
                <div className="w-32 h-48 bg-warmgrey border-2 border-ink flex items-center justify-center">
                  <BookOpen className="w-12 h-12 text-concrete" />
                </div>
              )}
              <div className="flex-1 space-y-3">
                <h3 className="text-xl font-heading font-bold text-ink">{bookData.title}</h3>
                <p className="text-concrete">
                  <span className="font-medium text-ink">Author:</span> {bookData.authors.join(', ')}
                </p>
                {bookData.publisher && (
                  <p className="text-concrete">
                    <span className="font-medium text-ink">Publisher:</span> {bookData.publisher}
                  </p>
                )}
                {bookData.publish_date && (
                  <p className="text-concrete">
                    <span className="font-medium text-ink">Published:</span> {bookData.publish_date}
                  </p>
                )}
                {bookData.subjects.length > 0 && (
                  <div className="flex flex-wrap gap-2 pt-2">
                    {bookData.subjects.slice(0, 3).map((subject, idx) => (
                      <span key={idx} className="px-2 py-1 bg-warmgrey text-xs font-medium text-ink">
                        {subject}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}
          <DialogFooter className="gap-2">
            <Button
              onClick={() => setShowConfirmation(false)}
              variant="outline"
              className="rounded-none border-2 border-ink"
            >
              Cancel
            </Button>
            <Button
              onClick={handleReadNow}
              className="bg-signal text-white hover:bg-[#B02015] rounded-none font-bold tracking-wide uppercase"
              data-testid="read-now-button"
            >
              Read Now
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}