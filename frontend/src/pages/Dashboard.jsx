import { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../App";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Badge } from "../components/ui/badge";
import { 
  Search, Upload, TrendingUp, Bell, Heart, Package, 
  History, ArrowRight, Image, X, Loader2, Tag, ShoppingBag
} from "lucide-react";
import { toast } from "sonner";

const Dashboard = () => {
  const navigate = useNavigate();
  const fileInputRef = useRef(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchLoading, setSearchLoading] = useState(false);
  const [imageFile, setImageFile] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);
  const [stats, setStats] = useState(null);
  const [recentSearches, setRecentSearches] = useState([]);
  const [categories, setCategories] = useState([]);
  const [supplierCategories, setSupplierCategories] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState(null);

  useEffect(() => {
    fetchDashboardData();
    fetchCategories();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const response = await api.get("/dashboard/stats");
      setStats(response.data);
      setRecentSearches(response.data.recent_searches || []);
    } catch (error) {
      console.error("Error fetching dashboard data:", error);
    }
  };

  const fetchCategories = async () => {
    try {
      const response = await api.get("/categories");
      setCategories(response.data.all_categories || []);
      setSupplierCategories(response.data.supplier_categories || []);
    } catch (error) {
      console.error("Error fetching categories:", error);
    }
  };

  const handleTextSearch = async (e) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;

    setSearchLoading(true);
    try {
      const payload = { query: searchQuery };
      if (selectedCategory) {
        payload.category = selectedCategory;
      }
      const response = await api.post("/search/text", payload);
      navigate("/search", { state: { results: response.data, query: searchQuery } });
    } catch (error) {
      toast.error("Erreur lors de la recherche");
    } finally {
      setSearchLoading(false);
    }
  };

  const handleImageSelect = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      setImageFile(file);
      const reader = new FileReader();
      reader.onloadend = () => {
        setImagePreview(reader.result);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleImageSearch = async () => {
    if (!imageFile) return;

    setSearchLoading(true);
    try {
      const formData = new FormData();
      formData.append("file", imageFile);
      
      const response = await api.post("/search/image", formData, {
        headers: { "Content-Type": "multipart/form-data" }
      });
      navigate("/search", { state: { results: response.data, query: "Image Search" } });
    } catch (error) {
      toast.error("Erreur lors de la recherche par image");
    } finally {
      setSearchLoading(false);
    }
  };

  const clearImage = () => {
    setImageFile(null);
    setImagePreview(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const getCategoryIcon = (cat) => {
    const icons = {
      "Électronique": "💻",
      "Mode": "👗",
      "Maison": "🏠",
      "Sport": "⚽",
      "Jouets": "🧸",
      "Livres": "📚",
      "Beauté": "💄",
    };
    return icons[cat] || "📦";
  };

  const statCards = [
    {
      title: "Fournisseurs",
      value: stats?.suppliers_count || 0,
      icon: Package,
      color: "text-blue-400",
      bgColor: "bg-blue-400/10",
      link: "/suppliers"
    },
    {
      title: "Alertes actives",
      value: stats?.active_alerts_count || 0,
      icon: Bell,
      color: "text-orange-400",
      bgColor: "bg-orange-400/10",
      link: "/alerts"
    },
    {
      title: "Favoris",
      value: stats?.favorites_count || 0,
      icon: Heart,
      color: "text-pink-400",
      bgColor: "bg-pink-400/10",
      link: "/favorites"
    },
    {
      title: "Recherches",
      value: stats?.total_searches || 0,
      icon: History,
      color: "text-lime-400",
      bgColor: "bg-lime-400/10",
      link: null
    }
  ];

  return (
    <div className="min-h-screen bg-zinc-950 pt-20 pb-12">
      <div className="max-w-7xl mx-auto px-6">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl md:text-4xl font-bold text-zinc-50 font-['Chivo'] mb-2">
            Dashboard
          </h1>
          <p className="text-zinc-400">Recherchez et comparez les prix de vos produits</p>
        </div>

        {/* Search Section */}
        <Card className="bg-zinc-900 border-zinc-800 mb-8 card-glow">
          <CardHeader>
            <CardTitle className="text-zinc-50 flex items-center gap-2">
              <Search className="w-5 h-5 text-lime-400" />
              Recherche de produit
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Category Filter */}
            <div className="space-y-3">
              <div className="flex items-center gap-2 mb-2">
                <Tag className="w-4 h-4 text-zinc-400" />
                <span className="text-zinc-400 text-sm font-medium">Filtrer par catégorie</span>
                {selectedCategory && (
                  <button
                    onClick={() => setSelectedCategory(null)}
                    className="text-xs text-zinc-500 hover:text-zinc-300 underline ml-2"
                  >
                    Effacer le filtre
                  </button>
                )}
              </div>
              <div className="flex flex-wrap gap-2">
                {categories.map((cat) => {
                  const isSupplierCat = supplierCategories.includes(cat);
                  const isSelected = selectedCategory === cat;
                  return (
                    <button
                      key={cat}
                      onClick={() => setSelectedCategory(isSelected ? null : cat)}
                      className={`
                        inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm font-medium
                        transition-all duration-200 border
                        ${isSelected
                          ? 'bg-lime-400/20 border-lime-400/50 text-lime-400 shadow-[0_0_10px_rgba(163,230,53,0.1)]'
                          : isSupplierCat
                            ? 'bg-zinc-800/80 border-zinc-700 text-zinc-300 hover:border-lime-400/30 hover:text-lime-400'
                            : 'bg-zinc-800/40 border-zinc-800 text-zinc-500 hover:border-zinc-700 hover:text-zinc-400'
                        }
                      `}
                    >
                      <span>{getCategoryIcon(cat)}</span>
                      <span>{cat}</span>
                      {isSupplierCat && (
                        <span className="w-1.5 h-1.5 rounded-full bg-lime-400 inline-block" title="Vous avez des fournisseurs dans cette catégorie"></span>
                      )}
                    </button>
                  );
                })}
              </div>
              {supplierCategories.length > 0 && (
                <p className="text-xs text-zinc-600 flex items-center gap-1.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-lime-400 inline-block"></span>
                  Catégories avec fournisseurs configurés
                </p>
              )}
            </div>

            {/* Text Search */}
            <form onSubmit={handleTextSearch} className="flex gap-3">
              <div className="flex-1 relative">
                <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-zinc-500" />
                <Input
                  data-testid="search-input"
                  type="text"
                  placeholder={selectedCategory 
                    ? `Rechercher dans ${selectedCategory} (ex: ${selectedCategory === "Électronique" ? "iPhone 15, Samsung Galaxy..." : selectedCategory === "Mode" ? "Nike Air Max, Adidas..." : "Produit..."})`
                    : "Rechercher un produit (ex: iPhone 15, Nike Air Max...)"
                  }
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-12 h-14 text-lg bg-zinc-950 border-zinc-800 focus:border-lime-500/50 focus:ring-lime-500/20"
                />
              </div>
              <Button
                data-testid="search-btn"
                type="submit"
                disabled={searchLoading || !searchQuery.trim()}
                className="h-14 px-8 bg-lime-400 text-zinc-950 hover:bg-lime-500 font-bold shadow-[0_0_20px_rgba(163,230,53,0.2)]"
              >
                {searchLoading ? (
                  <Loader2 className="w-5 h-5 animate-spin" />
                ) : (
                  <>
                    Rechercher
                    <ArrowRight className="ml-2 w-5 h-5" />
                  </>
                )}
              </Button>
            </form>

            {/* Selected Category Indicator */}
            {selectedCategory && (
              <div className="flex items-center gap-2 px-3 py-2 bg-lime-400/5 border border-lime-400/20 rounded-lg">
                <ShoppingBag className="w-4 h-4 text-lime-400" />
                <span className="text-sm text-zinc-300">
                  Recherche filtrée par catégorie : <strong className="text-lime-400">{selectedCategory}</strong>
                  {supplierCategories.includes(selectedCategory) && (
                    <span className="text-zinc-500 ml-2">
                      — vos fournisseurs dans cette catégorie seront comparés
                    </span>
                  )}
                </span>
              </div>
            )}

            {/* Divider */}
            <div className="flex items-center gap-4">
              <div className="flex-1 h-px bg-zinc-800"></div>
              <span className="text-zinc-500 text-sm">ou</span>
              <div className="flex-1 h-px bg-zinc-800"></div>
            </div>

            {/* Image Search */}
            <div className="space-y-4">
              <div className="flex items-center gap-3">
                <Image className="w-5 h-5 text-zinc-400" />
                <span className="text-zinc-300 font-medium">Recherche par image</span>
              </div>
              
              {!imagePreview ? (
                <div
                  onClick={() => fileInputRef.current?.click()}
                  className="border-2 border-dashed border-zinc-700 rounded-lg p-8 text-center cursor-pointer hover:border-lime-500/50 transition-colors"
                >
                  <Upload className="w-10 h-10 text-zinc-500 mx-auto mb-3" />
                  <p className="text-zinc-400 mb-1">Cliquez pour uploader une image</p>
                  <p className="text-zinc-500 text-sm">PNG, JPG jusqu'à 10MB</p>
                </div>
              ) : (
                <div className="relative">
                  <div className="flex items-center gap-4 p-4 bg-zinc-800/50 rounded-lg border border-zinc-700">
                    <img
                      src={imagePreview}
                      alt="Preview"
                      className="w-24 h-24 object-cover rounded-lg"
                    />
                    <div className="flex-1">
                      <p className="text-zinc-300 font-medium">{imageFile?.name}</p>
                      <p className="text-zinc-500 text-sm">
                        {(imageFile?.size / 1024 / 1024).toFixed(2)} MB
                      </p>
                    </div>
                    <div className="flex gap-2">
                      <Button
                        data-testid="image-search-btn"
                        onClick={handleImageSearch}
                        disabled={searchLoading}
                        className="bg-lime-400 text-zinc-950 hover:bg-lime-500 font-bold"
                      >
                        {searchLoading ? (
                          <Loader2 className="w-4 h-4 animate-spin" />
                        ) : (
                          <>
                            <Search className="w-4 h-4 mr-2" />
                            Rechercher
                          </>
                        )}
                      </Button>
                      <Button
                        data-testid="clear-image-btn"
                        variant="outline"
                        onClick={clearImage}
                        className="border-zinc-700 text-zinc-400 hover:bg-zinc-800"
                      >
                        <X className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                </div>
              )}
              
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                onChange={handleImageSelect}
                className="hidden"
                data-testid="image-upload-input"
              />
            </div>
          </CardContent>
        </Card>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          {statCards.map((stat) => (
            <Card
              key={stat.title}
              className={`bg-zinc-900 border-zinc-800 ${stat.link ? 'cursor-pointer hover:border-zinc-700' : ''} transition-all card-glow`}
              onClick={() => stat.link && navigate(stat.link)}
              data-testid={`stat-card-${stat.title.toLowerCase().replace(' ', '-')}`}
            >
              <CardContent className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <div className={`w-10 h-10 rounded-lg ${stat.bgColor} flex items-center justify-center`}>
                    <stat.icon className={`w-5 h-5 ${stat.color}`} />
                  </div>
                  {stat.link && (
                    <ArrowRight className="w-4 h-4 text-zinc-600" />
                  )}
                </div>
                <div className="text-3xl font-bold text-zinc-50 font-mono mb-1">
                  {stat.value}
                </div>
                <div className="text-sm text-zinc-400">{stat.title}</div>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Recent Searches */}
        <Card className="bg-zinc-900 border-zinc-800">
          <CardHeader>
            <CardTitle className="text-zinc-50 flex items-center gap-2">
              <History className="w-5 h-5 text-zinc-400" />
              Recherches récentes
            </CardTitle>
          </CardHeader>
          <CardContent>
            {recentSearches.length > 0 ? (
              <div className="space-y-3">
                {recentSearches.map((search, index) => (
                  <div
                    key={search.id || index}
                    className="flex items-center justify-between p-3 bg-zinc-800/50 rounded-lg hover:bg-zinc-800 transition-colors cursor-pointer"
                    onClick={() => {
                      setSearchQuery(search.query);
                      if (search.category) {
                        setSelectedCategory(search.category);
                      }
                    }}
                    data-testid={`recent-search-${index}`}
                  >
                    <div className="flex items-center gap-3">
                      {search.search_type === 'image' ? (
                        <Image className="w-4 h-4 text-zinc-500" />
                      ) : (
                        <Search className="w-4 h-4 text-zinc-500" />
                      )}
                      <span className="text-zinc-300">{search.query}</span>
                      {search.category && (
                        <Badge variant="outline" className="border-zinc-700 text-zinc-500 text-xs">
                          {search.category}
                        </Badge>
                      )}
                    </div>
                    <div className="flex items-center gap-4 text-sm">
                      <span className="text-zinc-500">
                        {search.results_count} résultats
                      </span>
                      {search.amazon_price && (
                        <span className="text-orange-400 font-mono text-xs">
                          Amazon: {search.amazon_price.toFixed(2)}€
                        </span>
                      )}
                      {search.lowest_price && (
                        <span className="text-lime-400 font-mono">
                          {search.lowest_price.toFixed(2)}€
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-zinc-500">
                <Search className="w-12 h-12 mx-auto mb-3 text-zinc-700" />
                <p>Aucune recherche récente</p>
                <p className="text-sm mt-1">Commencez par rechercher un produit</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default Dashboard;
