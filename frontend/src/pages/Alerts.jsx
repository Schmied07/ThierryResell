import { useState, useEffect } from "react";
import { api } from "../App";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Switch } from "../components/ui/switch";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "../components/ui/dialog";
import { 
  Plus, Bell, BellOff, Trash2, TrendingDown, 
  DollarSign, Loader2, Target
} from "lucide-react";
import { toast } from "sonner";

const Alerts = () => {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [formData, setFormData] = useState({
    product_name: "",
    product_url: "",
    target_price: "",
    current_price: ""
  });

  useEffect(() => {
    fetchAlerts();
  }, []);

  const fetchAlerts = async () => {
    try {
      const response = await api.get("/alerts");
      setAlerts(response.data);
    } catch (error) {
      toast.error("Erreur lors du chargement des alertes");
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await api.post("/alerts", {
        ...formData,
        target_price: parseFloat(formData.target_price),
        current_price: formData.current_price ? parseFloat(formData.current_price) : null
      });
      toast.success("Alerte créée !");
      setDialogOpen(false);
      setFormData({ product_name: "", product_url: "", target_price: "", current_price: "" });
      fetchAlerts();
    } catch (error) {
      toast.error("Erreur lors de la création de l'alerte");
    }
  };

  const handleToggle = async (id) => {
    try {
      const response = await api.put(`/alerts/${id}/toggle`);
      setAlerts(alerts.map(a => 
        a.id === id ? { ...a, is_active: response.data.is_active } : a
      ));
      toast.success(response.data.is_active ? "Alerte activée" : "Alerte désactivée");
    } catch (error) {
      toast.error("Erreur lors de la modification");
    }
  };

  const handleDelete = async (id) => {
    if (!confirm("Supprimer cette alerte ?")) return;
    try {
      await api.delete(`/alerts/${id}`);
      toast.success("Alerte supprimée !");
      fetchAlerts();
    } catch (error) {
      toast.error("Erreur lors de la suppression");
    }
  };

  const activeAlerts = alerts.filter(a => a.is_active);
  const inactiveAlerts = alerts.filter(a => !a.is_active);

  return (
    <div className="min-h-screen bg-zinc-950 pt-20 pb-12">
      <div className="max-w-7xl mx-auto px-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl md:text-4xl font-bold text-zinc-50 font-['Chivo'] mb-2">
              Alertes de prix
            </h1>
            <p className="text-zinc-400">
              Soyez notifié quand les prix atteignent votre cible
            </p>
          </div>
          <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
            <DialogTrigger asChild>
              <Button
                data-testid="add-alert-btn"
                className="bg-orange-500 hover:bg-orange-600 text-white font-bold"
              >
                <Plus className="w-4 h-4 mr-2" />
                Nouvelle alerte
              </Button>
            </DialogTrigger>
            <DialogContent className="bg-zinc-900 border-zinc-800">
              <DialogHeader>
                <DialogTitle className="text-zinc-50">Nouvelle alerte de prix</DialogTitle>
                <DialogDescription className="text-zinc-400">
                  Créez une alerte pour être notifié quand le prix baisse
                </DialogDescription>
              </DialogHeader>
              <form onSubmit={handleSubmit} className="space-y-4 mt-4">
                <div className="space-y-2">
                  <Label htmlFor="product_name" className="text-zinc-300">Nom du produit *</Label>
                  <Input
                    id="product_name"
                    data-testid="alert-product-input"
                    value={formData.product_name}
                    onChange={(e) => setFormData({ ...formData, product_name: e.target.value })}
                    className="bg-zinc-950 border-zinc-800 focus:border-orange-500/50"
                    placeholder="iPhone 15 Pro Max 256GB"
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="product_url" className="text-zinc-300">URL du produit</Label>
                  <Input
                    id="product_url"
                    data-testid="alert-url-input"
                    type="url"
                    value={formData.product_url}
                    onChange={(e) => setFormData({ ...formData, product_url: e.target.value })}
                    className="bg-zinc-950 border-zinc-800 focus:border-orange-500/50"
                    placeholder="https://amazon.com/product/..."
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="current_price" className="text-zinc-300">Prix actuel (€)</Label>
                    <Input
                      id="current_price"
                      data-testid="alert-current-price-input"
                      type="number"
                      step="0.01"
                      min="0"
                      value={formData.current_price}
                      onChange={(e) => setFormData({ ...formData, current_price: e.target.value })}
                      className="bg-zinc-950 border-zinc-800 focus:border-orange-500/50"
                      placeholder="149.99"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="target_price" className="text-zinc-300">Prix cible (€) *</Label>
                    <Input
                      id="target_price"
                      data-testid="alert-target-price-input"
                      type="number"
                      step="0.01"
                      min="0"
                      value={formData.target_price}
                      onChange={(e) => setFormData({ ...formData, target_price: e.target.value })}
                      className="bg-zinc-950 border-zinc-800 focus:border-orange-500/50"
                      placeholder="129.99"
                      required
                    />
                  </div>
                </div>
                <div className="flex gap-3 pt-4">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => setDialogOpen(false)}
                    className="flex-1 border-zinc-700 text-zinc-300 hover:bg-zinc-800"
                  >
                    Annuler
                  </Button>
                  <Button
                    type="submit"
                    data-testid="alert-submit-btn"
                    className="flex-1 bg-orange-500 hover:bg-orange-600 text-white font-bold"
                  >
                    Créer l'alerte
                  </Button>
                </div>
              </form>
            </DialogContent>
          </Dialog>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
          <Card className="bg-zinc-900 border-zinc-800">
            <CardContent className="p-6 flex items-center gap-4">
              <div className="w-12 h-12 rounded-lg bg-orange-400/10 flex items-center justify-center">
                <Bell className="w-6 h-6 text-orange-400" />
              </div>
              <div>
                <div className="text-2xl font-bold text-zinc-50 font-mono">
                  {activeAlerts.length}
                </div>
                <div className="text-sm text-zinc-400">Alertes actives</div>
              </div>
            </CardContent>
          </Card>
          <Card className="bg-zinc-900 border-zinc-800">
            <CardContent className="p-6 flex items-center gap-4">
              <div className="w-12 h-12 rounded-lg bg-lime-400/10 flex items-center justify-center">
                <TrendingDown className="w-6 h-6 text-lime-400" />
              </div>
              <div>
                <div className="text-2xl font-bold text-zinc-50 font-mono">
                  {alerts.filter(a => a.triggered).length}
                </div>
                <div className="text-sm text-zinc-400">Alertes déclenchées</div>
              </div>
            </CardContent>
          </Card>
          <Card className="bg-zinc-900 border-zinc-800">
            <CardContent className="p-6 flex items-center gap-4">
              <div className="w-12 h-12 rounded-lg bg-zinc-700/50 flex items-center justify-center">
                <BellOff className="w-6 h-6 text-zinc-400" />
              </div>
              <div>
                <div className="text-2xl font-bold text-zinc-50 font-mono">
                  {inactiveAlerts.length}
                </div>
                <div className="text-sm text-zinc-400">Alertes inactives</div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Alerts List */}
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="w-8 h-8 animate-spin text-orange-400" />
          </div>
        ) : alerts.length > 0 ? (
          <div className="space-y-4">
            {alerts.map((alert) => (
              <Card
                key={alert.id}
                className={`bg-zinc-900 border-zinc-800 ${!alert.is_active ? 'opacity-60' : ''} hover:border-zinc-700 transition-all`}
                data-testid={`alert-card-${alert.id}`}
              >
                <CardContent className="p-6">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <div className={`w-12 h-12 rounded-lg ${alert.triggered ? 'bg-lime-400/10' : 'bg-orange-400/10'} flex items-center justify-center`}>
                        {alert.triggered ? (
                          <TrendingDown className="w-6 h-6 text-lime-400" />
                        ) : (
                          <Target className="w-6 h-6 text-orange-400" />
                        )}
                      </div>
                      <div>
                        <h3 className="font-bold text-zinc-50">{alert.product_name}</h3>
                        {alert.product_url && (
                          <a
                            href={alert.product_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-sm text-zinc-500 hover:text-lime-400 transition-colors"
                          >
                            Voir le produit →
                          </a>
                        )}
                      </div>
                    </div>

                    <div className="flex items-center gap-6">
                      <div className="text-right">
                        {alert.current_price && (
                          <div className="text-sm text-zinc-500">
                            Prix actuel: <span className="font-mono text-zinc-300">{alert.current_price.toFixed(2)}€</span>
                          </div>
                        )}
                        <div className="flex items-center gap-2">
                          <span className="text-sm text-zinc-400">Cible:</span>
                          <span className="text-lg font-bold font-mono text-orange-400">
                            {alert.target_price.toFixed(2)}€
                          </span>
                        </div>
                      </div>

                      <div className="flex items-center gap-3">
                        <Switch
                          checked={alert.is_active}
                          onCheckedChange={() => handleToggle(alert.id)}
                          data-testid={`alert-toggle-${alert.id}`}
                        />
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleDelete(alert.id)}
                          className="text-zinc-400 hover:text-red-400"
                          data-testid={`alert-delete-${alert.id}`}
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>
                    </div>
                  </div>

                  {alert.triggered && (
                    <div className="mt-4 p-3 rounded-lg bg-lime-400/10 border border-lime-400/20">
                      <div className="flex items-center gap-2 text-lime-400">
                        <TrendingDown className="w-4 h-4" />
                        <span className="text-sm font-medium">
                          Alerte déclenchée ! Le prix cible a été atteint.
                        </span>
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>
        ) : (
          <Card className="bg-zinc-900 border-zinc-800">
            <CardContent className="py-16 text-center">
              <Bell className="w-16 h-16 mx-auto mb-4 text-zinc-700" />
              <h3 className="text-xl font-bold text-zinc-50 mb-2">
                Aucune alerte
              </h3>
              <p className="text-zinc-400 mb-6">
                Créez une alerte pour être notifié quand les prix baissent
              </p>
              <Button
                onClick={() => setDialogOpen(true)}
                className="bg-orange-500 hover:bg-orange-600 text-white font-bold"
              >
                <Plus className="w-4 h-4 mr-2" />
                Nouvelle alerte
              </Button>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
};

export default Alerts;
