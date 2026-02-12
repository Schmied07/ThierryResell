import { useState, useEffect } from "react";
import { api } from "../App";
import { Button } from "../components/ui/button";
import { Card, CardContent } from "../components/ui/card";
import { 
  Heart, Trash2, ExternalLink, Search, Loader2, Image
} from "lucide-react";
import { toast } from "sonner";

const Favorites = () => {
  const [favorites, setFavorites] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchFavorites();
  }, []);

  const fetchFavorites = async () => {
    try {
      const response = await api.get("/favorites");
      setFavorites(response.data);
    } catch (error) {
      toast.error("Erreur lors du chargement des favoris");
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id) => {
    if (!confirm("Supprimer ce favori ?")) return;
    try {
      await api.delete(`/favorites/${id}`);
      toast.success("Favori supprimé !");
      fetchFavorites();
    } catch (error) {
      toast.error("Erreur lors de la suppression");
    }
  };

  return (
    <div className="min-h-screen bg-zinc-950 pt-20 pb-12">
      <div className="max-w-7xl mx-auto px-6">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl md:text-4xl font-bold text-zinc-50 font-['Chivo'] mb-2">
            Favoris
          </h1>
          <p className="text-zinc-400">
            Vos recherches et produits sauvegardés
          </p>
        </div>

        {/* Stats */}
        <Card className="bg-zinc-900 border-zinc-800 mb-8">
          <CardContent className="p-6 flex items-center gap-4">
            <div className="w-12 h-12 rounded-lg bg-pink-400/10 flex items-center justify-center">
              <Heart className="w-6 h-6 text-pink-400" />
            </div>
            <div>
              <div className="text-2xl font-bold text-zinc-50 font-mono">
                {favorites.length}
              </div>
              <div className="text-sm text-zinc-400">Favoris enregistrés</div>
            </div>
          </CardContent>
        </Card>

        {/* Favorites Grid */}
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="w-8 h-8 animate-spin text-pink-400" />
          </div>
        ) : favorites.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {favorites.map((favorite) => (
              <Card
                key={favorite.id}
                className="bg-zinc-900 border-zinc-800 hover:border-zinc-700 transition-all card-glow overflow-hidden"
                data-testid={`favorite-card-${favorite.id}`}
              >
                {/* Image */}
                <div className="h-40 bg-zinc-800 relative">
                  {favorite.image_url ? (
                    <img
                      src={favorite.image_url}
                      alt={favorite.product_name}
                      className="w-full h-full object-cover"
                      onError={(e) => {
                        e.target.style.display = 'none';
                      }}
                    />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center">
                      <Image className="w-12 h-12 text-zinc-700" />
                    </div>
                  )}
                  <div className="absolute top-3 right-3">
                    <div className="w-8 h-8 rounded-full bg-pink-400/20 flex items-center justify-center">
                      <Heart className="w-4 h-4 text-pink-400 fill-pink-400" />
                    </div>
                  </div>
                </div>

                <CardContent className="p-4">
                  <h3 className="font-bold text-zinc-50 mb-2 line-clamp-2">
                    {favorite.product_name}
                  </h3>
                  
                  {favorite.search_query && (
                    <div className="flex items-center gap-2 text-zinc-500 text-sm mb-3">
                      <Search className="w-3 h-3" />
                      <span className="truncate">{favorite.search_query}</span>
                    </div>
                  )}

                  {favorite.notes && (
                    <p className="text-zinc-500 text-sm mb-4 line-clamp-2">
                      {favorite.notes}
                    </p>
                  )}

                  <div className="flex items-center justify-between pt-3 border-t border-zinc-800">
                    <span className="text-xs text-zinc-500">
                      {new Date(favorite.created_at).toLocaleDateString('fr-FR')}
                    </span>
                    <div className="flex gap-2">
                      {favorite.product_url && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => window.open(favorite.product_url, '_blank')}
                          className="text-zinc-400 hover:text-white"
                        >
                          <ExternalLink className="w-4 h-4" />
                        </Button>
                      )}
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleDelete(favorite.id)}
                        className="text-zinc-400 hover:text-red-400"
                        data-testid={`favorite-delete-${favorite.id}`}
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        ) : (
          <Card className="bg-zinc-900 border-zinc-800">
            <CardContent className="py-16 text-center">
              <Heart className="w-16 h-16 mx-auto mb-4 text-zinc-700" />
              <h3 className="text-xl font-bold text-zinc-50 mb-2">
                Aucun favori
              </h3>
              <p className="text-zinc-400 mb-6">
                Ajoutez des produits en favoris depuis les résultats de recherche
              </p>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
};

export default Favorites;
