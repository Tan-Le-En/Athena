import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { BookOpen, Search, Bookmark, Highlighter, ArrowLeft, Library, LogOut, User, X } from 'lucide-react';
import axios from 'axios';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Progress } from '@/components/ui/progress';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function Reader({ user, logout }) {
  const { isbn } = useParams();
  const navigate = useNavigate();
  const [bookData, setBookData] = useState(null);
  const [content, setContent] = useState('');
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [showSearch, setShowSearch] = useState(false);
  const [readProgress, setReadProgress] = useState(0);
  const [bookmarks, setBookmarks] = useState([]);
  const [showBookmarks, setShowBookmarks] = useState(false);
  const contentRef = useRef(null);

  useEffect(() => {
    loadBook();
    loadBookmarks();
  }, [isbn]);

  useEffect(() => {
    const handleScroll = () => {
      if (contentRef.current) {
        const element = contentRef.current;
        const scrollPercentage = (element.scrollTop / (element.scrollHeight - element.clientHeight)) * 100;
        setReadProgress(scrollPercentage);
        saveProgress(scrollPercentage);
      }
    };

    const element = contentRef.current;
    if (element) {
      element.addEventListener('scroll', handleScroll);
      return () => element.removeEventListener('scroll', handleScroll);
    }
  }, [content]);

  const loadBook = async () => {
    try {
      const token = localStorage.getItem('token');
      const [metadataRes, contentRes, progressRes] = await Promise.all([
        axios.get(`${API}/books/search/${isbn}`),
        axios.get(`${API}/books/content/${isbn}`, {
          headers: { Authorization: `Bearer ${token}` }
        }),
        axios.get(`${API}/progress/${isbn}`, {
          headers: { Authorization: `Bearer ${token}` }
        })
      ]);

      setBookData(metadataRes.data);
      setContent(contentRes.data.content);

      if (progressRes.data) {
        setReadProgress(progressRes.data.position);
        setTimeout(() => {
          if (contentRef.current) {
            const scrollPosition = (progressRes.data.position / 100) * (contentRef.current.scrollHeight - contentRef.current.clientHeight);
            contentRef.current.scrollTop = scrollPosition;
          }
        }, 100);
      }
    } catch (error) {
      toast.error('Failed to load book');
    } finally {
      setLoading(false);
    }
  };

  const saveProgress = async (position) => {
    try {
      const token = localStorage.getItem('token');
      await axios.post(
        `${API}/progress`,
        { isbn, position },
        { headers: { Authorization: `Bearer ${token}` } }
      );
    } catch (error) {
      console.error('Failed to save progress:', error);
    }
  };

  const loadBookmarks = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/bookmarks/${isbn}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setBookmarks(response.data);
    } catch (error) {
      console.error('Failed to load bookmarks:', error);
    }
  };

  const addBookmark = async () => {
    try {
      const token = localStorage.getItem('token');
      const selectedText = window.getSelection().toString().trim();
      if (!selectedText) {
        toast.error('Please select some text to bookmark');
        return;
      }

      await axios.post(
        `${API}/bookmarks`,
        { isbn, position: readProgress, text: selectedText.substring(0, 200) },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      toast.success('Bookmark added');
      loadBookmarks();
    } catch (error) {
      toast.error('Failed to add bookmark');
    }
  };

  const deleteBookmark = async (position) => {
    try {
      const token = localStorage.getItem('token');
      await axios.delete(`${API}/bookmarks/${isbn}/${position}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Bookmark removed');
      loadBookmarks();
    } catch (error) {
      toast.error('Failed to remove bookmark');
    }
  };

  const handleSearch = () => {
    if (!searchTerm.trim()) return;
    const results = [];
    const lines = content.split('\n');
    lines.forEach((line, index) => {
      if (line.toLowerCase().includes(searchTerm.toLowerCase())) {
        results.push({ line: index, text: line.trim() });
      }
    });
    setSearchResults(results);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-canvas">
        <div className="text-ink text-xl font-heading">Loading book...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-canvas flex flex-col">
      <Progress value={readProgress} className="h-1 rounded-none" />

      <header className="border-b-2 border-ink bg-paper sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 py-3 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button
              variant="ghost"
              onClick={() => navigate('/')}
              className="rounded-none"
              data-testid="back-button"
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back
            </Button>
            <div className="flex items-center gap-2">
              <BookOpen className="w-6 h-6 text-signal" />
              <div>
                <h1 className="font-heading font-bold text-sm">{bookData?.title}</h1>
                <p className="text-xs text-concrete">{bookData?.authors.join(', ')}</p>
              </div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              onClick={() => setShowSearch(true)}
              className="rounded-none"
              data-testid="search-in-book-button"
            >
              <Search className="w-4 h-4" />
            </Button>
            <Button
              variant="ghost"
              onClick={addBookmark}
              className="rounded-none"
              data-testid="add-bookmark-button"
            >
              <Bookmark className="w-4 h-4" />
            </Button>
            <Button
              variant="ghost"
              onClick={() => setShowBookmarks(true)}
              className="rounded-none"
              data-testid="view-bookmarks-button"
            >
              Bookmarks ({bookmarks.length})
            </Button>
            <Button
              variant="ghost"
              onClick={() => navigate('/library')}
              className="rounded-none"
            >
              <Library className="w-4 h-4" />
            </Button>
            <Button variant="ghost" onClick={logout} className="rounded-none">
              <LogOut className="w-4 h-4" />
            </Button>
          </div>
        </div>
      </header>

      <main className="flex-1 overflow-hidden">
        <ScrollArea className="h-[calc(100vh-120px)]" ref={contentRef} data-testid="book-reader-content">
          <div className="max-w-3xl mx-auto px-6 py-12 bg-paper shadow-sm min-h-full">
            <div className="reader-content text-lg leading-relaxed whitespace-pre-wrap">
              {content}
            </div>
          </div>
        </ScrollArea>
      </main>

      <Dialog open={showSearch} onOpenChange={setShowSearch}>
        <DialogContent className="rounded-none border-2 border-ink bg-paper max-w-2xl">
          <DialogHeader>
            <DialogTitle className="text-xl font-heading font-bold">Search in Book</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div className="flex gap-2">
              <Input
                placeholder="Search for text..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                className="flex-1 h-10 border-2 border-ink rounded-none"
                data-testid="search-text-input"
              />
              <Button
                onClick={handleSearch}
                className="bg-signal text-white hover:bg-[#B02015] rounded-none"
                data-testid="search-text-button"
              >
                Search
              </Button>
            </div>
            <ScrollArea className="h-96">
              {searchResults.length > 0 ? (
                <div className="space-y-2">
                  {searchResults.map((result, idx) => (
                    <div key={idx} className="p-3 bg-warmgrey border border-ink text-sm">
                      <span className="font-medium text-concrete">Line {result.line + 1}:</span>
                      <p className="mt-1 text-ink">{result.text}</p>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-center text-concrete py-8">
                  {searchTerm ? 'No results found' : 'Enter a search term'}
                </p>
              )}
            </ScrollArea>
          </div>
        </DialogContent>
      </Dialog>

      <Dialog open={showBookmarks} onOpenChange={setShowBookmarks}>
        <DialogContent className="rounded-none border-2 border-ink bg-paper max-w-2xl">
          <DialogHeader>
            <DialogTitle className="text-xl font-heading font-bold">Your Bookmarks</DialogTitle>
          </DialogHeader>
          <ScrollArea className="h-96">
            {bookmarks.length > 0 ? (
              <div className="space-y-3">
                {bookmarks.map((bookmark, idx) => (
                  <div key={idx} className="p-3 bg-warmgrey border border-ink relative">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => deleteBookmark(bookmark.position)}
                      className="absolute top-2 right-2 rounded-none h-6 w-6 p-0"
                    >
                      <X className="w-4 h-4" />
                    </Button>
                    <p className="text-sm text-ink pr-8">{bookmark.text}</p>
                    <p className="text-xs text-concrete mt-2">
                      Progress: {bookmark.position.toFixed(1)}%
                    </p>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-center text-concrete py-8">No bookmarks yet</p>
            )}
          </ScrollArea>
        </DialogContent>
      </Dialog>
    </div>
  );
}