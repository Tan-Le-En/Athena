import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Mail, ShieldCheck } from 'lucide-react';
import axios from 'axios';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Separator } from '@/components/ui/separator';

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
      toast.success('Welcome back.');
      navigate('/');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Authentication failed');
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
      toast.success('Membership confirmed.');
      navigate('/');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Registration failed');
    } finally {
      setLoading(false);
    }
  };

  const SocialButton = ({ label, icon }) => (
    <Button 
      variant="outline" 
      className="w-full h-12 rounded-none border-border font-sans font-medium uppercase tracking-wide text-xs hover:bg-muted transition-all"
      onClick={() => toast.info(`${label} integration enabled shortly.`)}
    >
      {icon && <span className="mr-2">{icon}</span>}
      Continue with {label}
    </Button>
  );

  return (
    <div className="min-h-screen bg-canvas flex font-sans text-foreground">
      {/* Editorial Image Section */}
      <div className="hidden lg:flex lg:w-1/2 relative overflow-hidden bg-ink text-paper">
        <img
          src="https://images.unsplash.com/photo-1507842217121-9e871e9992d9?q=80&w=2070&auto=format&fit=crop"
          alt="Library Interior"
          className="absolute inset-0 w-full h-full object-cover opacity-50 grayscale mix-blend-screen"
        />
        <div className="absolute inset-0 bg-ink/20" />
        
        <div className="relative z-10 flex flex-col justify-between p-16 h-full w-full border-r border-white/10">
            <div className="border-l-2 border-primary pl-6">
                <h1 className="text-8xl font-serif font-black tracking-tighter mb-2 italic">ATHENA</h1>
                <p className="font-serif text-2xl italic opacity-80">
                    The Archive of Human Thought.
                </p>
            </div>
            
            <div className="grid grid-cols-2 gap-12 border-t border-white/20 pt-8">
                <div>
                    <h3 className="font-sans font-bold uppercase tracking-widest text-[10px] mb-3 text-white/60">Issue No.</h3>
                    <p className="font-serif text-3xl">Vol. 01</p>
                </div>
                <div>
                     <h3 className="font-sans font-bold uppercase tracking-widest text-[10px] mb-3 text-white/60">Curated By</h3>
                    <p className="font-serif text-3xl">Tan Le En</p>
                </div>
            </div>
        </div>
      </div>

      {/* Auth Form Section */}
      <div className="w-full lg:w-1/2 flex items-center justify-center p-8 lg:p-16 bg-paper relative">
        <div className="w-full max-w-md space-y-12">
            
          <div className="text-center lg:text-left space-y-2">
            <h2 className="text-5xl font-serif text-ink tracking-tight">Member Access</h2>
            <p className="text-muted-foreground font-sans text-sm uppercase tracking-widest">Digital Verification Required</p>
          </div>

          <Tabs defaultValue="login" className="w-full">
            <TabsList className="grid w-full grid-cols-2 rounded-none bg-transparent border-b border-border p-0 gap-8 h-auto mb-10">
              <TabsTrigger 
                value="login" 
                className="rounded-none font-serif text-xl bg-transparent border-b-2 border-transparent data-[state=active]:border-ink data-[state=active]:shadow-none data-[state=active]:bg-transparent px-0 pb-2 transition-all opacity-50 data-[state=active]:opacity-100"
              >
                Sign In
              </TabsTrigger>
              <TabsTrigger 
                value="register" 
                className="rounded-none font-serif text-xl bg-transparent border-b-2 border-transparent data-[state=active]:border-ink data-[state=active]:shadow-none data-[state=active]:bg-transparent px-0 pb-2 transition-all opacity-50 data-[state=active]:opacity-100"
              >
                Membership
              </TabsTrigger>
            </TabsList>

            <TabsContent value="login" className="space-y-8 animate-in fade-in-50 duration-500">
              <form onSubmit={handleLogin} className="space-y-6">
                <div className="space-y-2 group">
                  <Label htmlFor="login-email" className="font-sans font-bold uppercase tracking-widest text-[10px] text-muted-foreground group-focus-within:text-ink transition-colors">Email Address</Label>
                  <Input
                    id="login-email"
                    type="email"
                    placeholder="name@example.com"
                    value={loginData.email}
                    onChange={(e) => setLoginData({ ...loginData, email: e.target.value })}
                    className="h-12 border-0 border-b border-border rounded-none bg-transparent focus-visible:ring-0 focus-visible:border-ink px-0 text-lg font-serif placeholder:text-muted-foreground/30 transition-all"
                    required
                  />
                </div>
                <div className="space-y-2 group">
                  <Label htmlFor="login-password" className="font-sans font-bold uppercase tracking-widest text-[10px] text-muted-foreground group-focus-within:text-ink transition-colors">Password</Label>
                  <Input
                    id="login-password"
                    type="password"
                    placeholder="••••••••"
                    value={loginData.password}
                    onChange={(e) => setLoginData({ ...loginData, password: e.target.value })}
                    className="h-12 border-0 border-b border-border rounded-none bg-transparent focus-visible:ring-0 focus-visible:border-ink px-0 text-lg font-serif placeholder:text-muted-foreground/30 transition-all"
                    required
                  />
                </div>
                <Button
                  type="submit"
                  disabled={loading}
                  className="w-full h-14 bg-ink text-paper hover:bg-ink/90 rounded-none font-sans font-bold tracking-widest uppercase text-xs mt-8"
                >
                  {loading ? 'Verifying...' : 'Authenticate'}
                </Button>
              </form>
            </TabsContent>

            <TabsContent value="register" className="space-y-8 animate-in fade-in-50 duration-500">
              <form onSubmit={handleRegister} className="space-y-6">
                <div className="space-y-2 group">
                  <Label htmlFor="register-name" className="font-sans font-bold uppercase tracking-widest text-[10px] text-muted-foreground group-focus-within:text-ink transition-colors">Full Name</Label>
                  <Input
                    id="register-name"
                    type="text"
                    placeholder="Jane Doe"
                    value={registerData.name}
                    onChange={(e) => setRegisterData({ ...registerData, name: e.target.value })}
                    className="h-12 border-0 border-b border-border rounded-none bg-transparent focus-visible:ring-0 focus-visible:border-ink px-0 text-lg font-serif placeholder:text-muted-foreground/30 transition-all"
                    required
                  />
                </div>
                <div className="space-y-2 group">
                  <Label htmlFor="register-email" className="font-sans font-bold uppercase tracking-widest text-[10px] text-muted-foreground group-focus-within:text-ink transition-colors">Email Address</Label>
                  <Input
                    id="register-email"
                    type="email"
                    placeholder="name@example.com"
                    value={registerData.email}
                    onChange={(e) => setRegisterData({ ...registerData, email: e.target.value })}
                    className="h-12 border-0 border-b border-border rounded-none bg-transparent focus-visible:ring-0 focus-visible:border-ink px-0 text-lg font-serif placeholder:text-muted-foreground/30 transition-all"
                    required
                  />
                </div>
                <div className="space-y-2 group">
                  <Label htmlFor="register-password" className="font-sans font-bold uppercase tracking-widest text-[10px] text-muted-foreground group-focus-within:text-ink transition-colors">Set Password</Label>
                  <Input
                    id="register-password"
                    type="password"
                    placeholder="••••••••"
                    value={registerData.password}
                    onChange={(e) => setRegisterData({ ...registerData, password: e.target.value })}
                    className="h-12 border-0 border-b border-border rounded-none bg-transparent focus-visible:ring-0 focus-visible:border-ink px-0 text-lg font-serif placeholder:text-muted-foreground/30 transition-all"
                    required
                  />
                </div>
                <Button
                  type="submit"
                  disabled={loading}
                  className="w-full h-14 bg-ink text-paper hover:bg-ink/90 rounded-none font-sans font-bold tracking-widest uppercase text-xs mt-8"
                >
                  {loading ? 'Processing...' : 'Initiate Membership'}
                </Button>
              </form>
            </TabsContent>
          </Tabs>

          <div className="space-y-6">
            <div className="flex items-center gap-4">
                <Separator className="flex-1" />
                <span className="font-serif italic text-muted-foreground text-sm">or connect via</span>
                <Separator className="flex-1" />
            </div>

            <div className="space-y-3">
                 <SocialButton label="Google" />
                 <SocialButton label="Apple" />
                 <SocialButton label="Facebook" />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}