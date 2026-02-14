import { Link, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../App";
import { Button } from "./ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "./ui/dropdown-menu";
import { 
  TrendingUp, LayoutDashboard, Package, Bell, Heart, 
  Settings, LogOut, User, Menu, X, FileSpreadsheet
} from "lucide-react";
import { useState } from "react";

const Navbar = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const navItems = [
    { path: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
    { path: "/suppliers", label: "Fournisseurs", icon: Package },
    { path: "/alerts", label: "Alertes", icon: Bell },
    { path: "/favorites", label: "Favoris", icon: Heart },
  ];

  const handleLogout = () => {
    logout();
    navigate("/");
  };

  const isActive = (path) => location.pathname === path;

  return (
    <nav className="fixed top-0 w-full z-50 border-b border-zinc-800/50 bg-zinc-950/80 backdrop-blur-xl">
      <div className="max-w-7xl mx-auto px-4 md:px-6">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link to="/dashboard" className="flex items-center gap-2" data-testid="nav-logo">
            <div className="w-9 h-9 rounded-lg bg-lime-400 flex items-center justify-center">
              <TrendingUp className="w-5 h-5 text-zinc-950" />
            </div>
            <span className="text-lg font-bold text-zinc-50 font-['Chivo'] hidden sm:block">
              Resell Corner
            </span>
          </Link>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center gap-1">
            {navItems.map((item) => (
              <Link
                key={item.path}
                to={item.path}
                data-testid={`nav-${item.label.toLowerCase()}`}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  isActive(item.path)
                    ? "bg-lime-400/10 text-lime-400"
                    : "text-zinc-400 hover:text-zinc-50 hover:bg-zinc-800/50"
                }`}
              >
                <item.icon className="w-4 h-4" />
                {item.label}
              </Link>
            ))}
          </div>

          {/* User Menu */}
          <div className="flex items-center gap-3">
            <Link to="/settings" data-testid="nav-settings">
              <Button
                variant="ghost"
                size="icon"
                className={`text-zinc-400 hover:text-white ${
                  isActive("/settings") ? "text-lime-400 bg-lime-400/10" : ""
                }`}
              >
                <Settings className="w-5 h-5" />
              </Button>
            </Link>

            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button
                  variant="ghost"
                  data-testid="user-menu-btn"
                  className="flex items-center gap-2 text-zinc-300 hover:text-white"
                >
                  <div className="w-8 h-8 rounded-full bg-lime-400/20 flex items-center justify-center">
                    <User className="w-4 h-4 text-lime-400" />
                  </div>
                  <span className="hidden sm:block text-sm">{user?.name}</span>
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-56 bg-zinc-900 border-zinc-800">
                <div className="px-3 py-2">
                  <p className="text-sm font-medium text-zinc-50">{user?.name}</p>
                  <p className="text-xs text-zinc-500">{user?.email}</p>
                </div>
                <DropdownMenuSeparator className="bg-zinc-800" />
                <DropdownMenuItem
                  onClick={() => navigate("/settings")}
                  className="text-zinc-300 focus:bg-zinc-800 focus:text-white cursor-pointer"
                >
                  <Settings className="w-4 h-4 mr-2" />
                  Paramètres
                </DropdownMenuItem>
                <DropdownMenuSeparator className="bg-zinc-800" />
                <DropdownMenuItem
                  onClick={handleLogout}
                  data-testid="logout-btn"
                  className="text-red-400 focus:bg-red-500/10 focus:text-red-400 cursor-pointer"
                >
                  <LogOut className="w-4 h-4 mr-2" />
                  Déconnexion
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>

            {/* Mobile Menu Button */}
            <Button
              variant="ghost"
              size="icon"
              className="md:hidden text-zinc-400"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              data-testid="mobile-menu-btn"
            >
              {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </Button>
          </div>
        </div>

        {/* Mobile Navigation */}
        {mobileMenuOpen && (
          <div className="md:hidden py-4 border-t border-zinc-800">
            <div className="flex flex-col gap-1">
              {navItems.map((item) => (
                <Link
                  key={item.path}
                  to={item.path}
                  onClick={() => setMobileMenuOpen(false)}
                  className={`flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-colors ${
                    isActive(item.path)
                      ? "bg-lime-400/10 text-lime-400"
                      : "text-zinc-400 hover:text-zinc-50 hover:bg-zinc-800/50"
                  }`}
                >
                  <item.icon className="w-5 h-5" />
                  {item.label}
                </Link>
              ))}
            </div>
          </div>
        )}
      </div>
    </nav>
  );
};

export default Navbar;
