import { useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { useAuth } from "../App";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/ui/tabs";
import { TrendingUp, Mail, Lock, User, ArrowLeft } from "lucide-react";
import { toast } from "sonner";

const AuthPage = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { login, register, user } = useAuth();
  const [loading, setLoading] = useState(false);
  
  // Redirect if already logged in
  if (user) {
    const from = location.state?.from?.pathname || "/dashboard";
    navigate(from, { replace: true });
  }

  const [loginForm, setLoginForm] = useState({ email: "", password: "" });
  const [registerForm, setRegisterForm] = useState({ email: "", password: "", name: "" });

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await login(loginForm.email, loginForm.password);
      toast.success("Connexion réussie !");
      const from = location.state?.from?.pathname || "/dashboard";
      navigate(from, { replace: true });
    } catch (error) {
      toast.error(error.response?.data?.detail || "Erreur de connexion");
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await register(registerForm.email, registerForm.password, registerForm.name);
      toast.success("Compte créé avec succès !");
      navigate("/dashboard");
    } catch (error) {
      toast.error(error.response?.data?.detail || "Erreur lors de l'inscription");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-zinc-950 flex flex-col noise-texture">
      {/* Back Button */}
      <div className="p-6">
        <Button
          data-testid="back-to-home-btn"
          variant="ghost"
          onClick={() => navigate("/")}
          className="text-zinc-400 hover:text-white"
        >
          <ArrowLeft className="w-4 h-4 mr-2" />
          Retour
        </Button>
      </div>

      {/* Auth Form */}
      <div className="flex-1 flex items-center justify-center px-6 pb-20">
        <div className="w-full max-w-md">
          {/* Logo */}
          <div className="flex items-center justify-center gap-3 mb-8">
            <div className="w-12 h-12 rounded-lg bg-lime-400 flex items-center justify-center">
              <TrendingUp className="w-7 h-7 text-zinc-950" />
            </div>
            <span className="text-2xl font-bold text-zinc-50 font-['Chivo']">Resell Corner</span>
          </div>

          <Card className="bg-zinc-900 border-zinc-800">
            <Tabs defaultValue="login" className="w-full">
              <CardHeader>
                <TabsList className="grid w-full grid-cols-2 bg-zinc-800/50">
                  <TabsTrigger 
                    data-testid="login-tab"
                    value="login" 
                    className="data-[state=active]:bg-zinc-700 data-[state=active]:text-white"
                  >
                    Connexion
                  </TabsTrigger>
                  <TabsTrigger 
                    data-testid="register-tab"
                    value="register"
                    className="data-[state=active]:bg-zinc-700 data-[state=active]:text-white"
                  >
                    Inscription
                  </TabsTrigger>
                </TabsList>
              </CardHeader>

              <CardContent>
                {/* Login Form */}
                <TabsContent value="login">
                  <form onSubmit={handleLogin} className="space-y-4">
                    <div className="space-y-2">
                      <Label htmlFor="login-email" className="text-zinc-300">Email</Label>
                      <div className="relative">
                        <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" />
                        <Input
                          id="login-email"
                          data-testid="login-email-input"
                          type="email"
                          placeholder="votre@email.com"
                          value={loginForm.email}
                          onChange={(e) => setLoginForm({ ...loginForm, email: e.target.value })}
                          className="pl-10 bg-zinc-950 border-zinc-800 focus:border-lime-500/50 focus:ring-lime-500/20"
                          required
                        />
                      </div>
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="login-password" className="text-zinc-300">Mot de passe</Label>
                      <div className="relative">
                        <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" />
                        <Input
                          id="login-password"
                          data-testid="login-password-input"
                          type="password"
                          placeholder="••••••••"
                          value={loginForm.password}
                          onChange={(e) => setLoginForm({ ...loginForm, password: e.target.value })}
                          className="pl-10 bg-zinc-950 border-zinc-800 focus:border-lime-500/50 focus:ring-lime-500/20"
                          required
                        />
                      </div>
                    </div>

                    <Button
                      data-testid="login-submit-btn"
                      type="submit"
                      disabled={loading}
                      className="w-full bg-lime-400 text-zinc-950 hover:bg-lime-500 font-bold shadow-[0_0_20px_rgba(163,230,53,0.2)]"
                    >
                      {loading ? "Connexion..." : "Se connecter"}
                    </Button>
                  </form>
                </TabsContent>

                {/* Register Form */}
                <TabsContent value="register">
                  <form onSubmit={handleRegister} className="space-y-4">
                    <div className="space-y-2">
                      <Label htmlFor="register-name" className="text-zinc-300">Nom</Label>
                      <div className="relative">
                        <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" />
                        <Input
                          id="register-name"
                          data-testid="register-name-input"
                          type="text"
                          placeholder="Votre nom"
                          value={registerForm.name}
                          onChange={(e) => setRegisterForm({ ...registerForm, name: e.target.value })}
                          className="pl-10 bg-zinc-950 border-zinc-800 focus:border-lime-500/50 focus:ring-lime-500/20"
                          required
                        />
                      </div>
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="register-email" className="text-zinc-300">Email</Label>
                      <div className="relative">
                        <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" />
                        <Input
                          id="register-email"
                          data-testid="register-email-input"
                          type="email"
                          placeholder="votre@email.com"
                          value={registerForm.email}
                          onChange={(e) => setRegisterForm({ ...registerForm, email: e.target.value })}
                          className="pl-10 bg-zinc-950 border-zinc-800 focus:border-lime-500/50 focus:ring-lime-500/20"
                          required
                        />
                      </div>
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="register-password" className="text-zinc-300">Mot de passe</Label>
                      <div className="relative">
                        <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" />
                        <Input
                          id="register-password"
                          data-testid="register-password-input"
                          type="password"
                          placeholder="••••••••"
                          value={registerForm.password}
                          onChange={(e) => setRegisterForm({ ...registerForm, password: e.target.value })}
                          className="pl-10 bg-zinc-950 border-zinc-800 focus:border-lime-500/50 focus:ring-lime-500/20"
                          required
                          minLength={6}
                        />
                      </div>
                      <p className="text-xs text-zinc-500">Minimum 6 caractères</p>
                    </div>

                    <Button
                      data-testid="register-submit-btn"
                      type="submit"
                      disabled={loading}
                      className="w-full bg-lime-400 text-zinc-950 hover:bg-lime-500 font-bold shadow-[0_0_20px_rgba(163,230,53,0.2)]"
                    >
                      {loading ? "Création..." : "Créer un compte"}
                    </Button>
                  </form>
                </TabsContent>
              </CardContent>
            </Tabs>
          </Card>

          <p className="text-center text-zinc-500 text-sm mt-6">
            En vous inscrivant, vous acceptez nos conditions d'utilisation
          </p>
        </div>
      </div>
    </div>
  );
};

export default AuthPage;
