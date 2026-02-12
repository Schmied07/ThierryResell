import { useState, useEffect } from "react";
import { api } from "../App";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Textarea } from "../components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "../components/ui/dialog";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "../components/ui/dropdown-menu";
import { 
  Plus, Package, Globe, MoreVertical, Pencil, Trash2, 
  ExternalLink, Loader2
} from "lucide-react";
import { toast } from "sonner";

const Suppliers = () => {
  const [suppliers, setSuppliers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingSupplier, setEditingSupplier] = useState(null);
  const [formData, setFormData] = useState({
    name: "",
    url: "",
    logo_url: "",
    category: "",
    notes: ""
  });

  useEffect(() => {
    fetchSuppliers();
  }, []);

  const fetchSuppliers = async () => {
    try {
      const response = await api.get("/suppliers");
      setSuppliers(response.data);
    } catch (error) {
      toast.error("Erreur lors du chargement des fournisseurs");
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editingSupplier) {
        await api.put(`/suppliers/${editingSupplier.id}`, formData);
        toast.success("Fournisseur modifié !");
      } else {
        await api.post("/suppliers", formData);
        toast.success("Fournisseur ajouté !");
      }
      setDialogOpen(false);
      resetForm();
      fetchSuppliers();
    } catch (error) {
      toast.error("Erreur lors de l'enregistrement");
    }
  };

  const handleDelete = async (id) => {
    if (!confirm("Supprimer ce fournisseur ?")) return;
    try {
      await api.delete(`/suppliers/${id}`);
      toast.success("Fournisseur supprimé !");
      fetchSuppliers();
    } catch (error) {
      toast.error("Erreur lors de la suppression");
    }
  };

  const handleEdit = (supplier) => {
    setEditingSupplier(supplier);
    setFormData({
      name: supplier.name,
      url: supplier.url,
      logo_url: supplier.logo_url || "",
      category: supplier.category || "",
      notes: supplier.notes || ""
    });
    setDialogOpen(true);
  };

  const resetForm = () => {
    setEditingSupplier(null);
    setFormData({
      name: "",
      url: "",
      logo_url: "",
      category: "",
      notes: ""
    });
  };

  const categories = ["Electronics", "Fashion", "Home", "Sports", "Toys", "Books", "Other"];

  return (
    <div className="min-h-screen bg-zinc-950 pt-20 pb-12">
      <div className="max-w-7xl mx-auto px-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl md:text-4xl font-bold text-zinc-50 font-['Chivo'] mb-2">
              Fournisseurs
            </h1>
            <p className="text-zinc-400">
              Gérez vos fournisseurs pour la comparaison de prix
            </p>
          </div>
          <Dialog open={dialogOpen} onOpenChange={(open) => {
            setDialogOpen(open);
            if (!open) resetForm();
          }}>
            <DialogTrigger asChild>
              <Button
                data-testid="add-supplier-btn"
                className="bg-lime-400 text-zinc-950 hover:bg-lime-500 font-bold shadow-[0_0_20px_rgba(163,230,53,0.2)]"
              >
                <Plus className="w-4 h-4 mr-2" />
                Ajouter un fournisseur
              </Button>
            </DialogTrigger>
            <DialogContent className="bg-zinc-900 border-zinc-800">
              <DialogHeader>
                <DialogTitle className="text-zinc-50">
                  {editingSupplier ? "Modifier le fournisseur" : "Nouveau fournisseur"}
                </DialogTitle>
                <DialogDescription className="text-zinc-400">
                  {editingSupplier 
                    ? "Modifiez les informations du fournisseur"
                    : "Ajoutez un nouveau fournisseur à votre liste"
                  }
                </DialogDescription>
              </DialogHeader>
              <form onSubmit={handleSubmit} className="space-y-4 mt-4">
                <div className="space-y-2">
                  <Label htmlFor="name" className="text-zinc-300">Nom *</Label>
                  <Input
                    id="name"
                    data-testid="supplier-name-input"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="bg-zinc-950 border-zinc-800 focus:border-lime-500/50"
                    placeholder="Amazon, eBay, AliExpress..."
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="url" className="text-zinc-300">URL *</Label>
                  <Input
                    id="url"
                    data-testid="supplier-url-input"
                    type="url"
                    value={formData.url}
                    onChange={(e) => setFormData({ ...formData, url: e.target.value })}
                    className="bg-zinc-950 border-zinc-800 focus:border-lime-500/50"
                    placeholder="https://example.com"
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="logo_url" className="text-zinc-300">URL du logo</Label>
                  <Input
                    id="logo_url"
                    data-testid="supplier-logo-input"
                    type="url"
                    value={formData.logo_url}
                    onChange={(e) => setFormData({ ...formData, logo_url: e.target.value })}
                    className="bg-zinc-950 border-zinc-800 focus:border-lime-500/50"
                    placeholder="https://example.com/logo.png"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="category" className="text-zinc-300">Catégorie</Label>
                  <select
                    id="category"
                    data-testid="supplier-category-select"
                    value={formData.category}
                    onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                    className="w-full h-10 px-3 rounded-md bg-zinc-950 border border-zinc-800 text-zinc-300 focus:border-lime-500/50 focus:outline-none"
                  >
                    <option value="">Sélectionner une catégorie</option>
                    {categories.map((cat) => (
                      <option key={cat} value={cat}>{cat}</option>
                    ))}
                  </select>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="notes" className="text-zinc-300">Notes</Label>
                  <Textarea
                    id="notes"
                    data-testid="supplier-notes-input"
                    value={formData.notes}
                    onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                    className="bg-zinc-950 border-zinc-800 focus:border-lime-500/50"
                    placeholder="Notes sur ce fournisseur..."
                    rows={3}
                  />
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
                    data-testid="supplier-submit-btn"
                    className="flex-1 bg-lime-400 text-zinc-950 hover:bg-lime-500 font-bold"
                  >
                    {editingSupplier ? "Modifier" : "Ajouter"}
                  </Button>
                </div>
              </form>
            </DialogContent>
          </Dialog>
        </div>

        {/* Suppliers Grid */}
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="w-8 h-8 animate-spin text-lime-400" />
          </div>
        ) : suppliers.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {suppliers.map((supplier) => (
              <Card
                key={supplier.id}
                className="bg-zinc-900 border-zinc-800 hover:border-zinc-700 transition-all card-glow"
                data-testid={`supplier-card-${supplier.id}`}
              >
                <CardContent className="p-6">
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex items-center gap-3">
                      {supplier.logo_url ? (
                        <img
                          src={supplier.logo_url}
                          alt={supplier.name}
                          className="w-12 h-12 rounded-lg object-cover bg-zinc-800"
                          onError={(e) => {
                            e.target.style.display = 'none';
                            e.target.nextSibling.style.display = 'flex';
                          }}
                        />
                      ) : null}
                      <div 
                        className={`w-12 h-12 rounded-lg bg-zinc-800 flex items-center justify-center ${supplier.logo_url ? 'hidden' : ''}`}
                      >
                        <Package className="w-6 h-6 text-zinc-500" />
                      </div>
                      <div>
                        <h3 className="font-bold text-zinc-50">{supplier.name}</h3>
                        {supplier.category && (
                          <span className="text-xs text-zinc-500">{supplier.category}</span>
                        )}
                      </div>
                    </div>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button
                          variant="ghost"
                          size="sm"
                          className="text-zinc-400 hover:text-white"
                          data-testid={`supplier-menu-${supplier.id}`}
                        >
                          <MoreVertical className="w-4 h-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end" className="bg-zinc-900 border-zinc-800">
                        <DropdownMenuItem
                          onClick={() => handleEdit(supplier)}
                          className="text-zinc-300 focus:bg-zinc-800 focus:text-white"
                        >
                          <Pencil className="w-4 h-4 mr-2" />
                          Modifier
                        </DropdownMenuItem>
                        <DropdownMenuItem
                          onClick={() => window.open(supplier.url, '_blank')}
                          className="text-zinc-300 focus:bg-zinc-800 focus:text-white"
                        >
                          <ExternalLink className="w-4 h-4 mr-2" />
                          Visiter
                        </DropdownMenuItem>
                        <DropdownMenuItem
                          onClick={() => handleDelete(supplier.id)}
                          className="text-red-400 focus:bg-red-500/10 focus:text-red-400"
                        >
                          <Trash2 className="w-4 h-4 mr-2" />
                          Supprimer
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </div>

                  <div className="flex items-center gap-2 text-zinc-400 text-sm mb-3">
                    <Globe className="w-4 h-4" />
                    <a
                      href={supplier.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="hover:text-lime-400 transition-colors truncate"
                    >
                      {supplier.url}
                    </a>
                  </div>

                  {supplier.notes && (
                    <p className="text-zinc-500 text-sm line-clamp-2">{supplier.notes}</p>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>
        ) : (
          <Card className="bg-zinc-900 border-zinc-800">
            <CardContent className="py-16 text-center">
              <Package className="w-16 h-16 mx-auto mb-4 text-zinc-700" />
              <h3 className="text-xl font-bold text-zinc-50 mb-2">
                Aucun fournisseur
              </h3>
              <p className="text-zinc-400 mb-6">
                Ajoutez vos premiers fournisseurs pour commencer à comparer les prix
              </p>
              <Button
                onClick={() => setDialogOpen(true)}
                className="bg-lime-400 text-zinc-950 hover:bg-lime-500 font-bold"
              >
                <Plus className="w-4 h-4 mr-2" />
                Ajouter un fournisseur
              </Button>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
};

export default Suppliers;
