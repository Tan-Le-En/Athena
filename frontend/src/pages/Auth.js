import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { BookOpen, Mail, Lock, User } from 'lucide-react';
import axios from 'axios';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function Auth({ onLogin }) {
  const [loginData, setLoginData] = useState({ email: '', password: '' });
  const [registerData, setRegisterData] = useState({ email: '', password: '', name: '' });
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const response = await axios.post(`${API}/auth/login`, loginData);
      onLogin(response.data.access_token, response.data.user);
      toast.success('Login successful!');
      navigate('/');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const response = await axios.post(`${API}/auth/register`, registerData);
      onLogin(response.data.access_token, response.data.user);
      toast.success('Account created successfully!');
      navigate('/');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Registration failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-canvas flex">
      <div className="hidden lg:flex lg:w-1/2 relative overflow-hidden">
        <img
          src="https://images.unsplash.com/photo-1613969673101-c982c30287f2?crop=entropy&cs=srgb&fm=jpg&q=85"
          alt="Library"
          className="absolute inset-0 w-full h-full object-cover"
        />
        <div className="absolute inset-0 bg-gradient-to-br from-signal/90 to-ink/90" />
        <div className="relative z-10 flex flex-col justify-center px-12 text-white">
          <BookOpen className="w-16 h-16 mb-6" strokeWidth={2} />
          <h1 className="text-5xl font-heading font-bold mb-4">ATHENAVISION</h1>
          <p className="text-xl leading-relaxed opacity-90">
            Instant access to literature. From ISBN to reading in under 2 seconds.
          </p>
          <div className="mt-12 space-y-4">
            <div className="flex items-start gap-3">
              <div className="w-8 h-8 bg-white/20 flex items-center justify-center rounded-none font-bold">1</div>
              <div>
                <h3 className="font-heading font-bold mb-1">Enter ISBN</h3>
                <p className="text-sm opacity-80">Input any 10 or 13-digit book identifier</p>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <div className="w-8 h-8 bg-white/20 flex items-center justify-center rounded-none font-bold">2</div>
              <div>
                <h3 className="font-heading font-bold mb-1">Instant Confirmation</h3>
                <p className="text-sm opacity-80">We fetch and verify the book metadata</p>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <div className="w-8 h-8 bg-white/20 flex items-center justify-center rounded-none font-bold">3</div>
              <div>
                <h3 className="font-heading font-bold mb-1">Start Reading</h3>
                <p className="text-sm opacity-80">Full-text access with progress tracking</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="w-full lg:w-1/2 flex items-center justify-center p-8">
        <div className="w-full max-w-md">
          <div className="mb-8 lg:hidden">
            <div className="flex items-center gap-3 mb-2">
              <BookOpen className="w-8 h-8 text-signal" strokeWidth={2.5} />
              <h1 className="text-2xl font-heading font-bold text-ink">ATHENAVISION</h1>
            </div>
            <p className="text-concrete">Your Digital Library Bridge</p>
          </div>

          <Tabs defaultValue="login" className="w-full">
            <TabsList className="grid w-full grid-cols-2 rounded-none border-2 border-ink h-12">
              <TabsTrigger value="login" className="rounded-none font-bold tracking-wide" data-testid="login-tab">Login</TabsTrigger>
              <TabsTrigger value="register" className="rounded-none font-bold tracking-wide" data-testid="register-tab">Register</TabsTrigger>
            </TabsList>

            <TabsContent value="login" className="mt-6">
              <form onSubmit={handleLogin} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="login-email" className="font-medium">Email</Label>
                  <div className="relative">
                    <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-concrete" />
                    <Input
                      id="login-email"
                      type="email"
                      placeholder="your@email.com"
                      value={loginData.email}
                      onChange={(e) => setLoginData({ ...loginData, email: e.target.value })}
                      className="pl-10 h-12 border-2 border-ink rounded-none bg-paper"
                      required
                      data-testid="login-email-input"
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="login-password" className="font-medium">Password</Label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-concrete" />
                    <Input
                      id="login-password"
                      type="password"
                      placeholder="••••••••"
                      value={loginData.password}
                      onChange={(e) => setLoginData({ ...loginData, password: e.target.value })}
                      className="pl-10 h-12 border-2 border-ink rounded-none bg-paper"
                      required
                      data-testid="login-password-input"
                    />
                  </div>
                </div>
                <Button
                  type="submit"
                  disabled={loading}
                  className="w-full h-12 bg-signal text-white hover:bg-[#B02015] rounded-none font-bold tracking-wide uppercase"
                  data-testid="login-submit-button"
                >
                  {loading ? 'Logging in...' : 'Login'}
                </Button>
              </form>
            </TabsContent>

            <TabsContent value="register" className="mt-6">
              <form onSubmit={handleRegister} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="register-name" className="font-medium">Name</Label>
                  <div className="relative">
                    <User className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-concrete" />
                    <Input
                      id="register-name"
                      type="text"
                      placeholder="Your Name"
                      value={registerData.name}
                      onChange={(e) => setRegisterData({ ...registerData, name: e.target.value })}
                      className="pl-10 h-12 border-2 border-ink rounded-none bg-paper"
                      required
                      data-testid="register-name-input"
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="register-email" className="font-medium">Email</Label>
                  <div className="relative">
                    <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-concrete" />
                    <Input
                      id="register-email"
                      type="email"
                      placeholder="your@email.com"
                      value={registerData.email}
                      onChange={(e) => setRegisterData({ ...registerData, email: e.target.value })}
                      className="pl-10 h-12 border-2 border-ink rounded-none bg-paper"
                      required
                      data-testid="register-email-input"
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="register-password" className="font-medium">Password</Label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-concrete" />
                    <Input
                      id="register-password"
                      type="password"
                      placeholder="••••••••"
                      value={registerData.password}
                      onChange={(e) => setRegisterData({ ...registerData, password: e.target.value })}
                      className="pl-10 h-12 border-2 border-ink rounded-none bg-paper"
                      required
                      data-testid="register-password-input"
                    />
                  </div>
                </div>
                <Button
                  type="submit"
                  disabled={loading}
                  className="w-full h-12 bg-signal text-white hover:bg-[#B02015] rounded-none font-bold tracking-wide uppercase"
                  data-testid="register-submit-button"
                >
                  {loading ? 'Creating Account...' : 'Create Account'}
                </Button>
              </form>
            </TabsContent>
          </Tabs>

          <div className="mt-8 text-center">
            <Button
              variant="ghost"
              onClick={() => navigate('/')}
              className="text-concrete hover:text-ink rounded-none"
            >
              ← Back to Home
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}