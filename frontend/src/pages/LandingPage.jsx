import { useNavigate } from "react-router-dom";
import { Button } from "../components/ui/button";
import { ArrowRight, Search, TrendingUp, Bell, Heart, DollarSign, BarChart3 } from "lucide-react";

const LandingPage = () => {
  const navigate = useNavigate();

  const features = [
    {
      icon: Search,
      title: "Recherche Intelligente",
      description: "Recherchez par texte ou uploadez une image pour trouver les meilleurs prix"
    },
    {
      icon: TrendingUp,
      title: "Comparaison Multi-Fournisseurs",
      description: "Comparez instantanément les prix entre tous vos fournisseurs"
    },
    {
      icon: BarChart3,
      title: "Historique des Prix",
      description: "Suivez l'évolution des prix avec des graphiques détaillés"
    },
    {
      icon: Bell,
      title: "Alertes de Prix",
      description: "Soyez notifié quand les prix atteignent votre cible"
    },
    {
      icon: DollarSign,
      title: "Calcul des Marges",
      description: "Calculez automatiquement vos profits potentiels"
    },
    {
      icon: Heart,
      title: "Favoris",
      description: "Sauvegardez vos recherches pour un accès rapide"
    }
  ];

  return (
    <div className="min-h-screen bg-zinc-950 noise-texture">
      {/* Hero Section */}
      <div className="relative overflow-hidden">
        {/* Background */}
        <div className="absolute inset-0 bg-dot-grid opacity-30"></div>
        <div className="absolute inset-0 bg-gradient-to-b from-zinc-950 via-transparent to-zinc-950"></div>
        
        {/* Nav */}
        <nav className="relative z-10 flex items-center justify-between px-6 py-4 max-w-7xl mx-auto">
          <div className="flex items-center gap-2">
            <div className="w-10 h-10 rounded-lg bg-lime-400 flex items-center justify-center">
              <TrendingUp className="w-6 h-6 text-zinc-950" />
            </div>
            <span className="text-xl font-bold text-zinc-50 font-['Chivo']">Resell Corner</span>
          </div>
          <Button 
            data-testid="nav-login-btn"
            onClick={() => navigate("/auth")}
            variant="outline"
            className="border-zinc-800 text-zinc-300 hover:bg-zinc-800 hover:text-white"
          >
            Connexion
          </Button>
        </nav>

        {/* Hero Content */}
        <div className="relative z-10 max-w-7xl mx-auto px-6 pt-20 pb-32">
          <div className="text-center max-w-4xl mx-auto">
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-lime-400/10 text-lime-400 text-sm font-medium mb-8 animate-fade-in">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-lime-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-lime-400"></span>
              </span>
              La plateforme de sourcing ultime
            </div>
            
            <h1 className="text-5xl md:text-6xl lg:text-7xl font-black text-zinc-50 tracking-tight mb-6 animate-fade-in stagger-1 font-['Chivo']">
              Trouvez les meilleurs
              <span className="text-lime-400"> prix</span>
              <br />en quelques secondes
            </h1>
            
            <p className="text-lg md:text-xl text-zinc-400 max-w-2xl mx-auto mb-10 animate-fade-in stagger-2">
              Comparez les prix entre fournisseurs, suivez les tendances, et maximisez vos marges avec notre plateforme de sourcing professionnelle.
            </p>
            
            <div className="flex flex-col sm:flex-row gap-4 justify-center animate-fade-in stagger-3">
              <Button
                data-testid="hero-get-started-btn"
                onClick={() => navigate("/auth")}
                className="bg-lime-400 text-zinc-950 hover:bg-lime-500 font-bold text-lg px-8 py-6 shadow-[0_0_30px_rgba(163,230,53,0.3)]"
              >
                Commencer gratuitement
                <ArrowRight className="ml-2 w-5 h-5" />
              </Button>
              <Button
                data-testid="hero-demo-btn"
                variant="outline"
                className="border-zinc-700 text-zinc-300 hover:bg-zinc-800 hover:text-white text-lg px-8 py-6"
                onClick={() => navigate("/auth")}
              >
                Voir la démo
              </Button>
            </div>
          </div>

          {/* Hero Image/Preview */}
          <div className="mt-20 relative animate-fade-in stagger-4">
            <div className="absolute -inset-4 bg-gradient-to-r from-lime-400/20 via-transparent to-lime-400/20 rounded-2xl blur-3xl"></div>
            <div className="relative bg-zinc-900 border border-zinc-800 rounded-xl overflow-hidden shadow-2xl">
              <div className="flex items-center gap-2 px-4 py-3 border-b border-zinc-800 bg-zinc-900/50">
                <div className="w-3 h-3 rounded-full bg-red-500"></div>
                <div className="w-3 h-3 rounded-full bg-yellow-500"></div>
                <div className="w-3 h-3 rounded-full bg-green-500"></div>
                <span className="ml-4 text-sm text-zinc-500">dashboard.resellcorner.com</span>
              </div>
              <div className="p-6 bg-dot-grid">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {/* Stats Cards Preview */}
                  <div className="bg-zinc-800/50 rounded-lg p-4 border border-zinc-700/50">
                    <div className="text-sm text-zinc-400 mb-1">Économies totales</div>
                    <div className="text-2xl font-bold text-lime-400 font-mono">+€12,450</div>
                  </div>
                  <div className="bg-zinc-800/50 rounded-lg p-4 border border-zinc-700/50">
                    <div className="text-sm text-zinc-400 mb-1">Fournisseurs</div>
                    <div className="text-2xl font-bold text-zinc-50 font-mono">24</div>
                  </div>
                  <div className="bg-zinc-800/50 rounded-lg p-4 border border-zinc-700/50">
                    <div className="text-sm text-zinc-400 mb-1">Alertes actives</div>
                    <div className="text-2xl font-bold text-orange-400 font-mono">18</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Features Section */}
      <section className="py-24 px-6 bg-zinc-900/50">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-zinc-50 mb-4 font-['Chivo']">
              Tout ce dont vous avez besoin
            </h2>
            <p className="text-zinc-400 max-w-2xl mx-auto">
              Une suite complète d'outils pour optimiser votre sourcing et maximiser vos profits
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {features.map((feature, index) => (
              <div
                key={feature.title}
                className={`group bg-zinc-900 border border-zinc-800 rounded-lg p-6 hover:border-zinc-700 transition-all duration-300 card-glow animate-fade-in stagger-${index + 1}`}
              >
                <div className="w-12 h-12 rounded-lg bg-lime-400/10 flex items-center justify-center mb-4 group-hover:bg-lime-400/20 transition-colors">
                  <feature.icon className="w-6 h-6 text-lime-400" />
                </div>
                <h3 className="text-lg font-bold text-zinc-50 mb-2">{feature.title}</h3>
                <p className="text-zinc-400 text-sm">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-24 px-6">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-3xl md:text-4xl font-bold text-zinc-50 mb-6 font-['Chivo']">
            Prêt à booster vos marges ?
          </h2>
          <p className="text-zinc-400 mb-10 text-lg">
            Rejoignez des milliers de resellers qui utilisent Resell Corner pour trouver les meilleurs deals
          </p>
          <Button
            data-testid="cta-start-btn"
            onClick={() => navigate("/auth")}
            className="bg-lime-400 text-zinc-950 hover:bg-lime-500 font-bold text-lg px-10 py-6 shadow-[0_0_30px_rgba(163,230,53,0.3)]"
          >
            Démarrer maintenant
            <ArrowRight className="ml-2 w-5 h-5" />
          </Button>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-zinc-800 py-8 px-6">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-lime-400 flex items-center justify-center">
              <TrendingUp className="w-4 h-4 text-zinc-950" />
            </div>
            <span className="text-sm text-zinc-400">© 2024 Resell Corner. Tous droits réservés.</span>
          </div>
          <div className="flex items-center gap-6 text-sm text-zinc-500">
            <a href="#" className="hover:text-zinc-300 transition-colors">Conditions</a>
            <a href="#" className="hover:text-zinc-300 transition-colors">Confidentialité</a>
            <a href="#" className="hover:text-zinc-300 transition-colors">Contact</a>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;
