import { useState, useEffect, useRef } from "react";
import { api } from "../App";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
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
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "../components/ui/tabs";
import {
  Upload, FileSpreadsheet, RefreshCw, Download, Trash2,
  Search, Filter, TrendingUp, Package, DollarSign, 
  Loader2, CheckCircle, AlertCircle, ArrowUpDown
} from "lucide-react";
import { toast } from "sonner";

const Catalog = () => {
  const fileInputRef = useRef(null);
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [products, setProducts] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(false);
  const [selectedProducts, setSelectedProducts] = useState([]);
  const [comparing, setComparing] = useState(false);
  
  // Filters
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedBrand, setSelectedBrand] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("");
  const [minMargin, setMinMargin] = useState("");
  const [comparedOnly, setComparedOnly] = useState(false);
  
  // Pagination
  const [currentPage, setCurrentPage] = useState(0);
  const [pageSize] = useState(50);
  const [totalProducts, setTotalProducts] = useState(0);

  useEffect(() => {
    fetchStats();
    fetchProducts();
  }, [currentPage, selectedBrand, selectedCategory, minMargin, comparedOnly, searchQuery]);

  const fetchStats = async () => {
    try {
      const response = await api.get("/catalog/stats");
      setStats(response.data);
    } catch (error) {
      console.error("Error fetching catalog stats:", error);
    }
  };

  const fetchProducts = async () => {
    setLoading(true);
    try {
      const params = {
        skip: currentPage * pageSize,
        limit: pageSize,
      };
      if (selectedBrand) params.brand = selectedBrand;
      if (selectedCategory) params.category = selectedCategory;
      if (minMargin) params.min_margin = parseFloat(minMargin);
      if (comparedOnly) params.compared_only = true;
      if (searchQuery) params.search = searchQuery;

      const response = await api.get("/catalog/products", { params });
      setProducts(response.data.products);
      setTotalProducts(response.data.total);
    } catch (error) {
      toast.error("Erreur lors du chargement des produits");
    } finally {
      setLoading(false);
    }
  };

  const handleFileSelect = (e) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      if (selectedFile.name.endsWith('.xlsx') || selectedFile.name.endsWith('.xls')) {
        setFile(selectedFile);
      } else {
        toast.error("Veuillez sélectionner un fichier Excel (.xlsx ou .xls)");
      }
    }
  };

  const handleImport = async () => {
    if (!file) {
      toast.error("Veuillez sélectionner un fichier");
      return;
    }

    setUploading(true);
    try {
      const formData = new FormData();
      formData.append("file", file);

      const response = await api.post("/catalog/import", formData, {
        headers: { "Content-Type": "multipart/form-data" }
      });

      toast.success(
        `✅ Import réussi ! ${response.data.imported} produits importés, ${response.data.skipped} ignorés (doublons)`
      );
      
      setFile(null);
      if (fileInputRef.current) fileInputRef.current.value = "";
      
      fetchStats();
      fetchProducts();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Erreur lors de l'import");
    } finally {
      setUploading(false);
    }
  };

  const handleCompareProduct = async (productId) => {
    setComparing(true);
    try {
      const response = await api.post(`/catalog/compare/${productId}`);
      toast.success(`Prix comparés pour ${response.data.product_name}`);
      fetchProducts();
      fetchStats();
    } catch (error) {
      toast.error("Erreur lors de la comparaison");
    } finally {
      setComparing(false);
    }
  };

  const handleCompareBatch = async () => {
    if (selectedProducts.length === 0) {
      toast.error("Sélectionnez au moins un produit");
      return;
    }

    setComparing(true);
    try {
      const response = await api.post("/catalog/compare-batch", selectedProducts);
      toast.success(
        `✅ ${response.data.success} produits comparés, ${response.data.failed} erreurs`
      );
      setSelectedProducts([]);
      fetchProducts();
      fetchStats();
    } catch (error) {
      toast.error("Erreur lors de la comparaison en lot");
    } finally {
      setComparing(false);
    }
  };

  const handleExport = async () => {
    try {
      const response = await api.get("/catalog/export", {
        params: { compared_only: comparedOnly },
        responseType: 'blob'
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `catalogue_export_${new Date().toISOString().split('T')[0]}.xlsx`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      
      toast.success("Export réussi !");
    } catch (error) {
      toast.error("Erreur lors de l'export");
    }
  };

  const handleDeleteAll = async () => {
    if (!window.confirm("Êtes-vous sûr de vouloir supprimer tous les produits du catalogue ?")) {
      return;
    }

    try {
      const response = await api.delete("/catalog/products");
      toast.success(`${response.data.deleted} produits supprimés`);
      fetchStats();
      fetchProducts();
    } catch (error) {
      toast.error("Erreur lors de la suppression");
    }
  };

  const toggleProductSelection = (productId) => {
    setSelectedProducts(prev =>
      prev.includes(productId)
        ? prev.filter(id => id !== productId)
        : [...prev, productId]
    );
  };

  const toggleSelectAll = () => {
    if (selectedProducts.length === products.length) {
      setSelectedProducts([]);
    } else {
      setSelectedProducts(products.map(p => p.id));
    }
  };

  const getMarginBadge = (percentage) => {
    if (!percentage) return <Badge variant="secondary">Non comparé</Badge>;
    if (percentage < 10) return <Badge variant="destructive">{percentage.toFixed(1)}%</Badge>;
    if (percentage < 30) return <Badge variant="warning" className="bg-orange-500">{percentage.toFixed(1)}%</Badge>;
    return <Badge variant="success" className="bg-green-500">{percentage.toFixed(1)}%</Badge>;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-zinc-950 via-zinc-900 to-zinc-950 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-white mb-2">📦 Catalogue Fournisseur</h1>
          <p className="text-zinc-400">
            Importez votre catalogue et comparez automatiquement les prix avec Amazon et Google
          </p>
        </div>

        {/* Stats Cards */}
        {stats && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
            <Card className="bg-zinc-900/50 border-zinc-800">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-zinc-400 text-sm">Produits totaux</p>
                    <p className="text-3xl font-bold text-white">{stats.total_products}</p>
                  </div>
                  <Package className="w-10 h-10 text-blue-400" />
                </div>
              </CardContent>
            </Card>

            <Card className="bg-zinc-900/50 border-zinc-800">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-zinc-400 text-sm">Produits comparés</p>
                    <p className="text-3xl font-bold text-white">{stats.compared_products}</p>
                  </div>
                  <CheckCircle className="w-10 h-10 text-green-400" />
                </div>
              </CardContent>
            </Card>

            <Card className="bg-zinc-900/50 border-zinc-800">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-zinc-400 text-sm">Marge potentielle</p>
                    <p className="text-3xl font-bold text-white">
                      {stats.total_potential_margin.toFixed(2)}€
                    </p>
                  </div>
                  <DollarSign className="w-10 h-10 text-yellow-400" />
                </div>
              </CardContent>
            </Card>

            <Card className="bg-zinc-900/50 border-zinc-800">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-zinc-400 text-sm">Meilleure marge</p>
                    <p className="text-3xl font-bold text-white">
                      {stats.best_opportunity_margin.toFixed(2)}€
                    </p>
                  </div>
                  <TrendingUp className="w-10 h-10 text-pink-400" />
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Main Tabs */}
        <Tabs defaultValue="products" className="space-y-6">
          <TabsList className="bg-zinc-900/50 border border-zinc-800">
            <TabsTrigger value="import">📤 Import</TabsTrigger>
            <TabsTrigger value="products">📋 Produits</TabsTrigger>
            <TabsTrigger value="opportunities">💎 Opportunités</TabsTrigger>
          </TabsList>

          {/* Import Tab */}
          <TabsContent value="import">
            <Card className="bg-zinc-900/50 border-zinc-800">
              <CardHeader>
                <CardTitle className="text-white">Importer un catalogue Excel</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="border-2 border-dashed border-zinc-700 rounded-lg p-12 text-center">
                  <FileSpreadsheet className="w-16 h-16 text-zinc-500 mx-auto mb-4" />
                  <p className="text-zinc-400 mb-4">
                    Glissez-déposez votre fichier Excel ou cliquez pour sélectionner
                  </p>
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept=".xlsx,.xls"
                    onChange={handleFileSelect}
                    className="hidden"
                  />
                  <Button
                    onClick={() => fileInputRef.current?.click()}
                    variant="outline"
                    className="border-zinc-700 text-white"
                  >
                    <Upload className="w-4 h-4 mr-2" />
                    Sélectionner un fichier
                  </Button>
                </div>

                {file && (
                  <div className="bg-zinc-800/50 p-4 rounded-lg flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <FileSpreadsheet className="w-8 h-8 text-green-400" />
                      <div>
                        <p className="text-white font-medium">{file.name}</p>
                        <p className="text-zinc-400 text-sm">
                          {(file.size / 1024).toFixed(2)} KB
                        </p>
                      </div>
                    </div>
                    <Button
                      onClick={handleImport}
                      disabled={uploading}
                      className="bg-gradient-to-r from-blue-500 to-purple-500"
                    >
                      {uploading ? (
                        <>
                          <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                          Import en cours...
                        </>
                      ) : (
                        <>
                          <Upload className="w-4 h-4 mr-2" />
                          Importer
                        </>
                      )}
                    </Button>
                  </div>
                )}

                <div className="bg-blue-500/10 border border-blue-500/20 rounded-lg p-4">
                  <h4 className="text-blue-400 font-semibold mb-2">📋 Format attendu</h4>
                  <p className="text-zinc-400 text-sm mb-2">
                    Votre fichier Excel doit contenir les colonnes suivantes :
                  </p>
                  <ul className="text-zinc-400 text-sm space-y-1 list-disc list-inside">
                    <li><strong>GTIN</strong> - Code-barres EAN du produit</li>
                    <li><strong>Name</strong> - Nom du produit</li>
                    <li><strong>Category</strong> - Catégorie</li>
                    <li><strong>Brand</strong> - Marque</li>
                    <li><strong>£ Lowest Price inc. shipping</strong> - Prix en GBP</li>
                  </ul>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Products Tab */}
          <TabsContent value="products">
            <Card className="bg-zinc-900/50 border-zinc-800">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="text-white">Liste des produits</CardTitle>
                  <div className="flex gap-2">
                    {selectedProducts.length > 0 && (
                      <Button
                        onClick={handleCompareBatch}
                        disabled={comparing}
                        className="bg-gradient-to-r from-green-500 to-emerald-500"
                      >
                        {comparing ? (
                          <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                        ) : (
                          <RefreshCw className="w-4 h-4 mr-2" />
                        )}
                        Comparer sélection ({selectedProducts.length})
                      </Button>
                    )}
                    <Button onClick={handleExport} variant="outline" className="border-zinc-700">
                      <Download className="w-4 h-4 mr-2" />
                      Exporter
                    </Button>
                    <Button
                      onClick={handleDeleteAll}
                      variant="destructive"
                      className="bg-red-500/20 border border-red-500/50"
                    >
                      <Trash2 className="w-4 h-4 mr-2" />
                      Tout supprimer
                    </Button>
                  </div>
                </div>

                {/* Filters */}
                <div className="grid grid-cols-1 md:grid-cols-5 gap-4 mt-4">
                  <Input
                    placeholder="🔍 Rechercher..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="bg-zinc-800 border-zinc-700 text-white"
                  />
                  
                  <select
                    value={selectedBrand}
                    onChange={(e) => setSelectedBrand(e.target.value)}
                    className="bg-zinc-800 border border-zinc-700 text-white rounded-md px-3 py-2"
                  >
                    <option value="">Toutes les marques</option>
                    {stats?.brands?.map(brand => (
                      <option key={brand} value={brand}>{brand}</option>
                    ))}
                  </select>

                  <select
                    value={selectedCategory}
                    onChange={(e) => setSelectedCategory(e.target.value)}
                    className="bg-zinc-800 border border-zinc-700 text-white rounded-md px-3 py-2"
                  >
                    <option value="">Toutes les catégories</option>
                    {stats?.categories?.map(cat => (
                      <option key={cat} value={cat}>{cat}</option>
                    ))}
                  </select>

                  <Input
                    type="number"
                    placeholder="Marge min %"
                    value={minMargin}
                    onChange={(e) => setMinMargin(e.target.value)}
                    className="bg-zinc-800 border-zinc-700 text-white"
                  />

                  <label className="flex items-center gap-2 text-white bg-zinc-800 border border-zinc-700 rounded-md px-3 py-2">
                    <input
                      type="checkbox"
                      checked={comparedOnly}
                      onChange={(e) => setComparedOnly(e.target.checked)}
                      className="rounded"
                    />
                    <span className="text-sm">Comparés uniquement</span>
                  </label>
                </div>
              </CardHeader>

              <CardContent>
                {loading ? (
                  <div className="flex items-center justify-center py-12">
                    <Loader2 className="w-8 h-8 text-blue-400 animate-spin" />
                  </div>
                ) : products.length === 0 ? (
                  <div className="text-center py-12">
                    <Package className="w-16 h-16 text-zinc-600 mx-auto mb-4" />
                    <p className="text-zinc-400">Aucun produit dans le catalogue</p>
                    <p className="text-zinc-500 text-sm">Importez un fichier Excel pour commencer</p>
                  </div>
                ) : (
                  <>
                    <div className="overflow-x-auto">
                      <Table>
                        <TableHeader>
                          <TableRow className="border-zinc-800">
                            <TableHead className="text-zinc-400">
                              <input
                                type="checkbox"
                                checked={selectedProducts.length === products.length}
                                onChange={toggleSelectAll}
                                className="rounded"
                              />
                            </TableHead>
                            <TableHead className="text-zinc-400">EAN</TableHead>
                            <TableHead className="text-zinc-400">Produit</TableHead>
                            <TableHead className="text-zinc-400">Marque</TableHead>
                            <TableHead className="text-zinc-400">Catégorie</TableHead>
                            <TableHead className="text-zinc-400">Prix fourni. (€)</TableHead>
                            <TableHead className="text-zinc-400">Prix Amazon (€)</TableHead>
                            <TableHead className="text-zinc-400">Meilleur prix (€)</TableHead>
                            <TableHead className="text-zinc-400">Marge</TableHead>
                            <TableHead className="text-zinc-400">Actions</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {products.map((product) => (
                            <TableRow key={product.id} className="border-zinc-800">
                              <TableCell>
                                <input
                                  type="checkbox"
                                  checked={selectedProducts.includes(product.id)}
                                  onChange={() => toggleProductSelection(product.id)}
                                  className="rounded"
                                />
                              </TableCell>
                              <TableCell className="text-zinc-400 font-mono text-xs">
                                {product.gtin}
                              </TableCell>
                              <TableCell className="text-white max-w-xs truncate">
                                {product.name}
                              </TableCell>
                              <TableCell className="text-zinc-300">{product.brand}</TableCell>
                              <TableCell className="text-zinc-400 text-sm">
                                {product.category}
                              </TableCell>
                              <TableCell className="text-white font-semibold">
                                {product.supplier_price_eur?.toFixed(2)}€
                              </TableCell>
                              <TableCell className="text-zinc-300">
                                {product.amazon_price_eur 
                                  ? `${product.amazon_price_eur.toFixed(2)}€`
                                  : "-"}
                              </TableCell>
                              <TableCell className="text-green-400 font-semibold">
                                {product.best_price_eur 
                                  ? `${product.best_price_eur.toFixed(2)}€`
                                  : "-"}
                              </TableCell>
                              <TableCell>
                                {product.margin_eur ? (
                                  <div>
                                    <div className="text-white font-semibold">
                                      {product.margin_eur.toFixed(2)}€
                                    </div>
                                    {getMarginBadge(product.margin_percentage)}
                                  </div>
                                ) : (
                                  <Badge variant="secondary">-</Badge>
                                )}
                              </TableCell>
                              <TableCell>
                                <Button
                                  size="sm"
                                  onClick={() => handleCompareProduct(product.id)}
                                  disabled={comparing}
                                  variant="outline"
                                  className="border-zinc-700 text-white"
                                >
                                  <RefreshCw className="w-3 h-3" />
                                </Button>
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </div>

                    {/* Pagination */}
                    <div className="flex items-center justify-between mt-4">
                      <p className="text-zinc-400 text-sm">
                        Affichage {currentPage * pageSize + 1} à{" "}
                        {Math.min((currentPage + 1) * pageSize, totalProducts)} sur {totalProducts}
                      </p>
                      <div className="flex gap-2">
                        <Button
                          onClick={() => setCurrentPage(p => Math.max(0, p - 1))}
                          disabled={currentPage === 0}
                          variant="outline"
                          size="sm"
                          className="border-zinc-700"
                        >
                          Précédent
                        </Button>
                        <Button
                          onClick={() => setCurrentPage(p => p + 1)}
                          disabled={(currentPage + 1) * pageSize >= totalProducts}
                          variant="outline"
                          size="sm"
                          className="border-zinc-700"
                        >
                          Suivant
                        </Button>
                      </div>
                    </div>
                  </>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Opportunities Tab */}
          <TabsContent value="opportunities">
            <OpportunitiesTab />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

const OpportunitiesTab = () => {
  const [opportunities, setOpportunities] = useState([]);
  const [loading, setLoading] = useState(false);
  const [minMargin, setMinMargin] = useState("0");

  useEffect(() => {
    fetchOpportunities();
  }, [minMargin]);

  const fetchOpportunities = async () => {
    setLoading(true);
    try {
      const response = await api.get("/catalog/opportunities", {
        params: {
          min_margin_percentage: parseFloat(minMargin) || 0,
          limit: 100
        }
      });
      setOpportunities(response.data.opportunities);
    } catch (error) {
      toast.error("Erreur lors du chargement des opportunités");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card className="bg-zinc-900/50 border-zinc-800">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-white">💎 Meilleures opportunités de revente</CardTitle>
          <div className="flex items-center gap-2">
            <span className="text-zinc-400 text-sm">Marge min:</span>
            <Input
              type="number"
              placeholder="0"
              value={minMargin}
              onChange={(e) => setMinMargin(e.target.value)}
              className="w-24 bg-zinc-800 border-zinc-700 text-white"
            />
            <span className="text-zinc-400 text-sm">%</span>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="w-8 h-8 text-blue-400 animate-spin" />
          </div>
        ) : opportunities.length === 0 ? (
          <div className="text-center py-12">
            <TrendingUp className="w-16 h-16 text-zinc-600 mx-auto mb-4" />
            <p className="text-zinc-400">Aucune opportunité trouvée</p>
            <p className="text-zinc-500 text-sm">
              Comparez d'abord les prix de vos produits
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {opportunities.map((product, index) => (
              <div
                key={product.id}
                className="bg-zinc-800/50 rounded-lg p-6 border border-zinc-700 hover:border-zinc-600 transition-colors"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <span className="text-2xl font-bold text-zinc-500">
                        #{index + 1}
                      </span>
                      <div>
                        <h3 className="text-white font-semibold">{product.name}</h3>
                        <p className="text-zinc-400 text-sm">
                          {product.brand} • {product.category}
                        </p>
                      </div>
                    </div>

                    <div className="grid grid-cols-4 gap-4 mt-4">
                      <div>
                        <p className="text-zinc-500 text-xs mb-1">Prix fournisseur</p>
                        <p className="text-white font-semibold">
                          {product.supplier_price_eur.toFixed(2)}€
                        </p>
                      </div>
                      <div>
                        <p className="text-zinc-500 text-xs mb-1">Prix Amazon</p>
                        <p className="text-white font-semibold">
                          {product.amazon_price_eur?.toFixed(2)}€
                        </p>
                      </div>
                      <div>
                        <p className="text-zinc-500 text-xs mb-1">Meilleur prix</p>
                        <p className="text-green-400 font-semibold">
                          {product.best_price_eur.toFixed(2)}€
                        </p>
                      </div>
                      <div>
                        <p className="text-zinc-500 text-xs mb-1">Marge potentielle</p>
                        <p className="text-2xl font-bold text-green-400">
                          {product.margin_eur.toFixed(2)}€
                        </p>
                        <Badge variant="success" className="bg-green-500 mt-1">
                          +{product.margin_percentage.toFixed(1)}%
                        </Badge>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default Catalog;
