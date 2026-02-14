import { useState, useEffect } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { api } from "../App";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Badge } from "../components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "../components/ui/table";
import {
  ArrowLeft, TrendingUp, TrendingDown, ExternalLink, Heart, Bell,
  Package, DollarSign, BarChart3, Minus
} from "lucide-react";
import { toast } from "sonner";
// Temporarily commenting out recharts import due to compilation issue
// import {
//   LineChart,
//   Line,
//   XAxis,
//   YAxis,
//   CartesianGrid,
//   Tooltip,
//   ResponsiveContainer,
//   Area,
//   AreaChart
// } from "recharts";

const SearchResults = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { results, query } = location.state || {};
  const [priceHistory, setPriceHistory] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!results) {
      navigate("/dashboard");
      return;
    }
    // Generate mock price history
    const data = [];
    const basePrice = results?.average_price || 100;
    for (let i = 30; i >= 0; i--) {
      const date = new Date();
      date.setDate(date.getDate() - i);
      data.push({
        date: date.toLocaleDateString('fr-FR', { day: '2-digit', month: 'short' }),
        price: basePrice * (0.9 + Math.random() * 0.2),
        amazon: basePrice * (0.85 + Math.random() * 0.3),
        ebay: basePrice * (0.8 + Math.random() * 0.4),
      });
    }
    setPriceHistory(data);
  }, [results, navigate]);

  const handleAddFavorite = async () => {
    try {
      await api.post("/favorites", {
        product_name: results?.product_name,
        search_query: query,
        image_url: results?.image_url
      });
      toast.success("Ajouté aux favoris !");
    } catch (error) {
      toast.error("Erreur lors de l'ajout aux favoris");
    }
  };

  const handleCreateAlert = async () => {
    try {
      await api.post("/alerts", {
        product_name: results?.product_name,
        target_price: results?.lowest_price * 0.9,
        current_price: results?.lowest_price
      });
      toast.success("Alerte créée !");
    } catch (error) {
      toast.error("Erreur lors de la création de l'alerte");
    }
  };

  if (!results) return null;

  // Temporarily commented out due to compilation issue
  // const CustomTooltip = ({ active, payload, label }) => {
  //   if (active && payload && payload.length) {
  //     return (
  //       <div className="bg-zinc-900/95 backdrop-blur border border-zinc-800 rounded-lg p-3 shadow-xl">
  //         <p className="text-zinc-400 text-sm mb-2">{label}</p>
  //         {payload.map((entry, index) => (
  //           <p key={index} className="text-sm font-mono" style={{ color: entry.color }}>
  //             {entry.name}: {entry.value.toFixed(2)}€
  //           </p>
  //         ))}
  //       </div>
  //     );
  //   }
  //   return null;
  // };

  return (
    <div className="min-h-screen bg-zinc-950 pt-20 pb-12">
      <div className="max-w-7xl mx-auto px-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center gap-4">
            <Button
              data-testid="back-btn"
              variant="ghost"
              onClick={() => navigate("/dashboard")}
              className="text-zinc-400 hover:text-white"
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              Retour
            </Button>
            <div>
              <h1 className="text-2xl md:text-3xl font-bold text-zinc-50 font-['Chivo']">
                {results.product_name}
              </h1>
              <p className="text-zinc-400 text-sm mt-1">
                {results.comparisons?.length || 0} fournisseurs comparés
              </p>
            </div>
          </div>
          <div className="flex gap-2">
            <Button
              data-testid="add-favorite-btn"
              variant="outline"
              onClick={handleAddFavorite}
              className="border-zinc-700 text-zinc-300 hover:bg-zinc-800"
            >
              <Heart className="w-4 h-4 mr-2" />
              Favoris
            </Button>
            <Button
              data-testid="create-alert-btn"
              onClick={handleCreateAlert}
              className="bg-orange-500 hover:bg-orange-600 text-white"
            >
              <Bell className="w-4 h-4 mr-2" />
              Créer alerte
            </Button>
          </div>
        </div>

        {/* Stats Overview */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <Card className="bg-zinc-900 border-zinc-800">
            <CardContent className="p-6">
              <div className="flex items-center gap-3 mb-2">
                <div className="w-8 h-8 rounded-lg bg-lime-400/10 flex items-center justify-center">
                  <TrendingDown className="w-4 h-4 text-lime-400" />
                </div>
                <span className="text-zinc-400 text-sm">Prix le plus bas</span>
              </div>
              <div className="text-2xl font-bold text-lime-400 font-mono">
                {results.lowest_price?.toFixed(2)}€
              </div>
            </CardContent>
          </Card>

          <Card className="bg-zinc-900 border-zinc-800">
            <CardContent className="p-6">
              <div className="flex items-center gap-3 mb-2">
                <div className="w-8 h-8 rounded-lg bg-red-400/10 flex items-center justify-center">
                  <TrendingUp className="w-4 h-4 text-red-400" />
                </div>
                <span className="text-zinc-400 text-sm">Prix le plus haut</span>
              </div>
              <div className="text-2xl font-bold text-red-400 font-mono">
                {results.highest_price?.toFixed(2)}€
              </div>
            </CardContent>
          </Card>

          <Card className="bg-zinc-900 border-zinc-800">
            <CardContent className="p-6">
              <div className="flex items-center gap-3 mb-2">
                <div className="w-8 h-8 rounded-lg bg-blue-400/10 flex items-center justify-center">
                  <DollarSign className="w-4 h-4 text-blue-400" />
                </div>
                <span className="text-zinc-400 text-sm">Prix moyen</span>
              </div>
              <div className="text-2xl font-bold text-zinc-50 font-mono">
                {results.average_price?.toFixed(2)}€
              </div>
            </CardContent>
          </Card>

          <Card className="bg-zinc-900 border-zinc-800">
            <CardContent className="p-6">
              <div className="flex items-center gap-3 mb-2">
                <div className="w-8 h-8 rounded-lg bg-purple-400/10 flex items-center justify-center">
                  <BarChart3 className="w-4 h-4 text-purple-400" />
                </div>
                <span className="text-zinc-400 text-sm">Économie potentielle</span>
              </div>
              <div className="text-2xl font-bold text-purple-400 font-mono">
                {(results.highest_price - results.lowest_price)?.toFixed(2)}€
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Price Comparison Table */}
          <div className="lg:col-span-8">
            <Card className="bg-zinc-900 border-zinc-800">
              <CardHeader>
                <CardTitle className="text-zinc-50 flex items-center gap-2">
                  <Package className="w-5 h-5 text-lime-400" />
                  Comparaison des prix
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="rounded-lg border border-zinc-800 overflow-hidden">
                  <Table>
                    <TableHeader>
                      <TableRow className="bg-zinc-800/50 hover:bg-zinc-800/50">
                        <TableHead className="text-zinc-400 font-medium">Fournisseur</TableHead>
                        <TableHead className="text-zinc-400 font-medium text-right">Prix</TableHead>
                        <TableHead className="text-zinc-400 font-medium text-right">Livraison</TableHead>
                        <TableHead className="text-zinc-400 font-medium text-right">Total</TableHead>
                        <TableHead className="text-zinc-400 font-medium text-center">Stock</TableHead>
                        <TableHead className="text-zinc-400 font-medium text-right">Marge</TableHead>
                        <TableHead className="text-zinc-400 font-medium"></TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {results.comparisons?.map((comparison, index) => (
                        <TableRow
                          key={index}
                          className={`hover:bg-zinc-800/30 ${index === 0 ? 'bg-lime-400/5' : ''}`}
                          data-testid={`comparison-row-${index}`}
                        >
                          <TableCell className="font-medium text-zinc-200">
                            <div className="flex items-center gap-2">
                              {index === 0 && (
                                <Badge className="bg-lime-400/20 text-lime-400 text-xs">
                                  Meilleur
                                </Badge>
                              )}
                              {comparison.supplier}
                            </div>
                          </TableCell>
                          <TableCell className="text-right font-mono text-zinc-300">
                            {comparison.price.toFixed(2)}€
                          </TableCell>
                          <TableCell className="text-right font-mono text-zinc-400">
                            {comparison.shipping > 0 ? `${comparison.shipping.toFixed(2)}€` : 'Gratuit'}
                          </TableCell>
                          <TableCell className="text-right font-mono font-bold text-zinc-50">
                            {comparison.total_price.toFixed(2)}€
                          </TableCell>
                          <TableCell className="text-center">
                            <Badge
                              variant="outline"
                              className={
                                comparison.availability === 'In Stock'
                                  ? 'border-lime-500/50 text-lime-400'
                                  : comparison.availability === 'Low Stock'
                                  ? 'border-orange-500/50 text-orange-400'
                                  : 'border-zinc-600 text-zinc-400'
                              }
                            >
                              {comparison.availability}
                            </Badge>
                          </TableCell>
                          <TableCell className="text-right">
                            <span
                              className={`font-mono font-medium ${
                                comparison.profit_margin > 0
                                  ? 'text-lime-400'
                                  : comparison.profit_margin < 0
                                  ? 'text-red-400'
                                  : 'text-zinc-400'
                              }`}
                            >
                              {comparison.profit_margin > 0 ? '+' : ''}
                              {comparison.profit_margin?.toFixed(1)}%
                            </span>
                          </TableCell>
                          <TableCell>
                            <Button
                              variant="ghost"
                              size="sm"
                              className="text-zinc-400 hover:text-white"
                              onClick={() => window.open(comparison.supplier_url, '_blank')}
                              data-testid={`visit-supplier-${index}`}
                            >
                              <ExternalLink className="w-4 h-4" />
                            </Button>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Price History Chart */}
          <div className="lg:col-span-4">
            <Card className="bg-zinc-900 border-zinc-800 h-full">
              <CardHeader>
                <CardTitle className="text-zinc-50 flex items-center gap-2">
                  <BarChart3 className="w-5 h-5 text-lime-400" />
                  Historique des prix
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-64">
                  {/* Chart temporarily disabled due to compilation issue */}
                  <div className="h-full flex items-center justify-center bg-zinc-800/30 rounded-lg border border-zinc-700">
                    <div className="text-center">
                      <BarChart3 className="w-12 h-12 text-zinc-600 mx-auto mb-2" />
                      <p className="text-zinc-500 text-sm">Graphique temporairement indisponible</p>
                      <p className="text-zinc-600 text-xs">Historique des prix sur 30 jours</p>
                    </div>
                  </div>
                </div>

                {/* Detected Labels */}
                {results.detected_labels?.length > 0 && (
                  <div className="mt-6">
                    <p className="text-zinc-400 text-sm mb-2">Labels détectés:</p>
                    <div className="flex flex-wrap gap-2">
                      {results.detected_labels.map((label, index) => (
                        <Badge
                          key={index}
                          variant="outline"
                          className="border-zinc-700 text-zinc-400"
                        >
                          {label}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SearchResults;
