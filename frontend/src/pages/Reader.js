import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { BookOpen, Search, Bookmark, Highlighter, ArrowLeft, Library, LogOut, User, X, Share2, Type } from 'lucide-react';
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

  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => {
    loadBook();
    loadBookmarks();
  }, [isbn]);

  // eslint-disable-next-line react-hooks/exhaustive-deps
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
      toast.success('Passage marked');
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
        <div className="text-center py-12">
            <div className="text-ink text-xl font-serif italic animate-pulse">Loading manuscript...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-canvas flex flex-col font-sans">
      <Progress value={readProgress} className="h-1 rounded-none bg-ink/10" indicatorClassName="bg-signal" />

      <header className="border-b border-border bg-paper/95 backdrop-blur sticky top-0 z-50">
        <div className="max-w-5xl mx-auto px-6 py-3 flex items-center justify-between">
          <div className="flex items-center gap-6">
            <Button
              variant="ghost"
              onClick={() => navigate('/')}
              className="rounded-none hover:bg-transparent px-0 text-muted-foreground hover:text-ink transition-colors"
              data-testid="back-button"
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              <span className="uppercase text-[10px] tracking-widest font-bold">Return</span>
            </Button>
            <div className="h-4 w-px bg-border hidden sm:block"></div>
            <div className="flex items-center gap-3">
              <span className="font-serif font-bold italic text-lg">{bookData?.title}</span>
              <span className="text-xs text-muted-foreground font-sans uppercase tracking-wider hidden sm:inline-block">/ {bookData?.authors[0]}</span>
            </div>
          </div>
          <div className="flex items-center gap-1">
            <Button
              variant="ghost"
              onClick={() => setShowSearch(true)}
              className="rounded-none w-10 h-10 p-0 hover:bg-ink/5"
              title="Search Text"
            >
              <Search className="w-4 h-4" />
            </Button>
            <Button
              variant="ghost"
              onClick={addBookmark}
              className="rounded-none w-10 h-10 p-0 hover:bg-ink/5"
              title="Bookmark Selection"
            >
              <Bookmark className="w-4 h-4" />
            </Button>
            <Button
              variant="ghost"
              onClick={() => setShowBookmarks(true)}
              className="rounded-none h-10 px-3 hover:bg-ink/5 gap-2"
              title="View Bookmarks"
            >
              <Type className="w-4 h-4" />
              <span className="text-[10px] font-bold uppercase tracking-widest hidden sm:inline-block">{bookmarks.length}</span>
            </Button>
            
            <div className="h-4 w-px bg-border mx-2"></div>

             <Button
              variant="ghost"
              onClick={() => {
                navigator.clipboard.writeText(window.location.href);
                toast.success('Link copied to clipboard');
              }}
              className="rounded-none w-10 h-10 p-0 hover:bg-ink/5"
              title="Share Link"
            >
              <Share2 className="w-4 h-4" />
            </Button>
            
            <Button 
                variant="ghost" 
                onClick={logout} 
                className="rounded-none w-10 h-10 p-0 hover:bg-destructive hover:text-white transition-colors"
                title="Logout"
            >
              <LogOut className="w-4 h-4" />
            </Button>
          </div>
        </div>
      </header>

      <main className="flex-1 overflow-hidden relative">
        <ScrollArea className="h-[calc(100vh-60px)]" ref={contentRef} data-testid="book-reader-content">
          <div className="max-w-2xl mx-auto px-6 py-16 bg-paper min-h-full border-x border-dashed border-ink/10 shadow-[0_0_50px_-12px_rgba(0,0,0,0.05)]">
            <div className="reader-content text-lg md:text-xl leading-loose font-serif text-ink/90 selection:bg-signal/20 selection:text-ink space-y-8">
              {content.split('\n\n').map((paragraph, pIdx) => (
                <p key={pIdx} className="relative first-of-type:first-letter:text-7xl first-of-type:first-letter:font-serif first-of-type:first-letter:float-left first-of-type:first-letter:mr-3 first-of-type:first-letter:mt-2 first-of-type:first-letter:text-signal first-of-type:first-letter:leading-[0.8]">
                  {paragraph}
                </p>
              ))}
            </div>
            <div className="mt-32 pt-12 border-t border-ink/10 text-center">
                <p className="font-sans text-[10px] uppercase tracking-widest text-muted-foreground font-bold italic">The Artifact Ends Here</p>
                <div className="w-8 h-8 border border-ink/20 rotate-45 mx-auto mt-6 flex items-center justify-center">
                   <div className="w-2 h-2 bg-ink/20 rounded-full" />
                </div>
            </div>
          </div>
        </ScrollArea>
      </main>

      <Dialog open={showSearch} onOpenChange={setShowSearch}>
        <DialogContent className="rounded-none border-2 border-ink bg-paper max-w-2xl">
          <DialogHeader>
            <DialogTitle className="text-xl font-serif font-bold italic">Search Manuscript</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div className="flex gap-2">
              <Input
                placeholder="Find text..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                className="flex-1 h-12 border-b border-ink/20 rounded-none bg-transparent font-serif text-lg px-0 focus-visible:ring-0 focus-visible:border-ink placeholder:text-muted-foreground/50 transition-colors"
                data-testid="search-text-input"
              />
              <Button
                onClick={handleSearch}
                className="bg-ink text-paper hover:bg-ink/90 rounded-none font-sans font-bold uppercase tracking-widest text-xs px-6"
                data-testid="search-text-button"
              >
                Find
              </Button>
            </div>
            <ScrollArea className="h-96 pr-4">
              {searchResults.length > 0 ? (
                <div className="space-y-4 pt-4">
                  {searchResults.map((result, idx) => (
                    <div key={idx} className="p-4 bg-warmgrey/30 border-l-2 border-ink/20 hover:border-signal transition-colors group cursor-default">
                      <div className="flex justify-between items-center mb-2">
                         <span className="font-sans text-[10px] uppercase tracking-widest font-bold text-muted-foreground">Line {result.line + 1}</span>
                      </div>
                      <p className="font-serif text-ink group-hover:text-black">{result.text}</p>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="flex flex-col items-center justify-center h-full text-muted-foreground py-12">
                   <Search className="w-8 h-8 mb-4 opacity-20" />
                   <p className="font-serif italic">Enter a term to search the text.</p>
                </div>
              )}
            </ScrollArea>
          </div>
        </DialogContent>
      </Dialog>

      <Dialog open={showBookmarks} onOpenChange={setShowBookmarks}>
        <DialogContent className="rounded-none border-2 border-ink bg-paper max-w-2xl">
          <DialogHeader>
            <DialogTitle className="text-xl font-serif font-bold italic">Saved Passages</DialogTitle>
          </DialogHeader>
          <ScrollArea className="h-96 pr-4">
            {bookmarks.length > 0 ? (
              <div className="space-y-6 pt-2">
                {bookmarks.map((bookmark, idx) => (
                  <div key={idx} className="relative pl-6 border-l border-ink/20 hover:border-signal transition-colors group">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => deleteBookmark(bookmark.position)}
                      className="absolute top-0 right-0 rounded-none h-6 w-6 p-0 opacity-0 group-hover:opacity-100 transition-opacity hover:bg-destructive hover:text-white"
                    >
                      <X className="w-3 h-3" />
                    </Button>
                    <blockquote className="font-serif text-lg italic text-ink mb-2 pr-8">
                        "{bookmark.text}"
                    </blockquote>
                    <p className="font-sans text-[10px] uppercase tracking-widest text-muted-foreground">
                      Location: {bookmark.position.toFixed(1)}%
                    </p>
                  </div>
                ))}
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center h-full text-muted-foreground py-12">
                   <Bookmark className="w-8 h-8 mb-4 opacity-20" />
                   <p className="font-serif italic">No passages saved yet.</p>
              </div>
            )}
          </ScrollArea>
        </DialogContent>
      </Dialog>
    </div>
  );
}