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
  Loader2, CheckCircle, AlertCircle, ArrowUpDown,
  ChevronDown, ChevronUp, X, ShoppingCart, Globe, Store,
  ArrowRight, Percent, Info
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
  const [expandedProduct, setExpandedProduct] = useState(null);
  const [compareResult, setCompareResult] = useState(null);
  
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
  const [apiKeysConfigured, setApiKeysConfigured] = useState(false);

  useEffect(() => {
    fetchStats();
    fetchProducts();
    fetchApiKeyStatus();
  }, [currentPage, selectedBrand, selectedCategory, minMargin, comparedOnly, searchQuery]);

  const fetchStats = async () => {
    try {
      const response = await api.get("/catalog/stats");
      setStats(response.data);
    } catch (error) {
      console.error("Error fetching catalog stats:", error);
    }
  };

  const fetchApiKeyStatus = async () => {
    try {
      const response = await api.get("/settings/api-keys");
      const { keepa_api_key_set, google_api_key_set } = response.data;
      setApiKeysConfigured(keepa_api_key_set || google_api_key_set);
    } catch (error) {
      console.error("Error checking API keys:", error);
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
        timeout: 120000
      });

      toast.success(
        `Import réussi ! ${response.data.imported} produits importés, ${response.data.skipped} ignorés`
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
    setExpandedProduct(productId);
    try {
      const response = await api.post(`/catalog/compare/${productId}`);
      setCompareResult(response.data);
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
        `${response.data.success} produits comparés, ${response.data.failed} erreurs`
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

  const getMarginBadge = (marginEur, marginPct) => {
    if (marginEur === null || marginEur === undefined) return <Badge variant="secondary" className="text-xs">Non comparé</Badge>;
    if (marginEur < 0) return <Badge className="bg-red-500/20 text-red-400 border border-red-500/30 text-xs">{marginPct?.toFixed(1)}%</Badge>;
    if (marginPct < 10) return <Badge className="bg-orange-500/20 text-orange-400 border border-orange-500/30 text-xs">{marginPct?.toFixed(1)}%</Badge>;
    if (marginPct < 25) return <Badge className="bg-yellow-500/20 text-yellow-400 border border-yellow-500/30 text-xs">{marginPct?.toFixed(1)}%</Badge>;
    return <Badge className="bg-green-500/20 text-green-400 border border-green-500/30 text-xs">{marginPct?.toFixed(1)}%</Badge>;
  };

  const getCheapestSourceBadge = (source) => {
    if (!source) return null;
    if (source === "supplier") {
      return <Badge className="bg-blue-500/20 text-blue-400 border border-blue-500/30 text-xs"><Store className="w-3 h-3 mr-1" />Fournisseur</Badge>;
    }
    return <Badge className="bg-purple-500/20 text-purple-400 border border-purple-500/30 text-xs"><Globe className="w-3 h-3 mr-1" />Google</Badge>;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-zinc-950 via-zinc-900 to-zinc-950 p-4 md:p-8">
      <div className="max-w-[1600px] mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl md:text-4xl font-bold text-white mb-2">Catalogue Fournisseur</h1>
          <p className="text-zinc-400">
            Importez votre catalogue, comparez les prix Amazon (Keepa) et Google, et calculez vos marges de revente
          </p>
        </div>

        {/* Stats Cards */}
        {stats && (
          <div className="grid grid-cols-2 md:grid-cols-5 gap-3 mb-8">
            <Card className="bg-zinc-900/50 border-zinc-800">
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-zinc-500 text-xs font-medium uppercase tracking-wider">Produits</p>
                    <p className="text-2xl font-bold text-white mt-1">{stats.total_products}</p>
                  </div>
                  <Package className="w-8 h-8 text-blue-400/60" />
                </div>
              </CardContent>
            </Card>

            <Card className="bg-zinc-900/50 border-zinc-800">
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-zinc-500 text-xs font-medium uppercase tracking-wider">Comparés</p>
                    <p className="text-2xl font-bold text-white mt-1">{stats.compared_products}</p>
                  </div>
                  <CheckCircle className="w-8 h-8 text-green-400/60" />
                </div>
              </CardContent>
            </Card>

            <Card className="bg-zinc-900/50 border-zinc-800">
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-zinc-500 text-xs font-medium uppercase tracking-wider">Rentables</p>
                    <p className="text-2xl font-bold text-green-400 mt-1">{stats.profitable_products || 0}</p>
                  </div>
                  <TrendingUp className="w-8 h-8 text-green-400/60" />
                </div>
              </CardContent>
            </Card>

            <Card className="bg-zinc-900/50 border-zinc-800">
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-zinc-500 text-xs font-medium uppercase tracking-wider">Marge totale</p>
                    <p className="text-2xl font-bold text-white mt-1">{stats.total_potential_margin?.toFixed(0)}€</p>
                  </div>
                  <DollarSign className="w-8 h-8 text-yellow-400/60" />
                </div>
              </CardContent>
            </Card>

            <Card className="bg-zinc-900/50 border-zinc-800">
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-zinc-500 text-xs font-medium uppercase tracking-wider">Marge moy.</p>
                    <p className="text-2xl font-bold text-white mt-1">{stats.avg_margin_percentage?.toFixed(1)}%</p>
                  </div>
                  <Percent className="w-8 h-8 text-pink-400/60" />
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Info banner about Amazon fees */}
        <div className={`${apiKeysConfigured ? 'bg-green-500/10 border-green-500/20' : 'bg-amber-500/10 border-amber-500/20'} border rounded-lg px-4 py-3 mb-6 flex items-center gap-3`}>
          {apiKeysConfigured ? (
            <CheckCircle className="w-5 h-5 text-green-400 shrink-0" />
          ) : (
            <Info className="w-5 h-5 text-amber-400 shrink-0" />
          )}
          <p className={`${apiKeysConfigured ? 'text-green-200' : 'text-amber-200'} text-sm`}>
            <strong>Calcul des marges :</strong> Prix Amazon (vente) - Prix d'achat (le moins cher entre fournisseur et Google) - Frais Amazon (15% TTC).
            {apiKeysConfigured ? (
              <> Les données sont récupérées via vos <strong>clés API réelles</strong> (Keepa / Google).</>
            ) : (
              <> Les données affichées sont <strong>simulées</strong> tant que les clés API Keepa et Google ne sont pas configurées dans les Paramètres.</>
            )}
          </p>
        </div>

        {/* Main Tabs */}
        <Tabs defaultValue="products" className="space-y-6">
          <TabsList className="bg-zinc-900/50 border border-zinc-800">
            <TabsTrigger value="import">Import</TabsTrigger>
            <TabsTrigger value="products">Produits</TabsTrigger>
            <TabsTrigger value="opportunities">Opportunités</TabsTrigger>
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
                  <h4 className="text-blue-400 font-semibold mb-2">Format attendu</h4>
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
                <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
                  <CardTitle className="text-white">Liste des produits</CardTitle>
                  <div className="flex flex-wrap gap-2">
                    {selectedProducts.length > 0 && (
                      <Button
                        onClick={handleCompareBatch}
                        disabled={comparing}
                        className="bg-gradient-to-r from-green-500 to-emerald-500 text-white"
                      >
                        {comparing ? (
                          <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                        ) : (
                          <RefreshCw className="w-4 h-4 mr-2" />
                        )}
                        Comparer ({selectedProducts.length})
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
                      Supprimer tout
                    </Button>
                  </div>
                </div>

                {/* Filters */}
                <div className="grid grid-cols-1 md:grid-cols-5 gap-3 mt-4">
                  <Input
                    placeholder="Rechercher..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="bg-zinc-800 border-zinc-700 text-white"
                  />
                  
                  <select
                    value={selectedBrand}
                    onChange={(e) => setSelectedBrand(e.target.value)}
                    className="bg-zinc-800 border border-zinc-700 text-white rounded-md px-3 py-2 text-sm"
                  >
                    <option value="">Toutes les marques</option>
                    {stats?.brands?.map(brand => (
                      <option key={brand} value={brand}>{brand}</option>
                    ))}
                  </select>

                  <select
                    value={selectedCategory}
                    onChange={(e) => setSelectedCategory(e.target.value)}
                    className="bg-zinc-800 border border-zinc-700 text-white rounded-md px-3 py-2 text-sm"
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
                            <TableHead className="text-zinc-400 w-10">
                              <input
                                type="checkbox"
                                checked={selectedProducts.length === products.length && products.length > 0}
                                onChange={toggleSelectAll}
                                className="rounded"
                              />
                            </TableHead>
                            <TableHead className="text-zinc-400">Produit</TableHead>
                            <TableHead className="text-zinc-400 text-right">Fournisseur</TableHead>
                            <TableHead className="text-zinc-400 text-right">
                              <div className="flex items-center justify-end gap-1">
                                <ShoppingCart className="w-3 h-3" />
                                Amazon
                              </div>
                            </TableHead>
                            <TableHead className="text-zinc-400 text-right">
                              <div className="flex items-center justify-end gap-1">
                                <Globe className="w-3 h-3" />
                                Google
                              </div>
                            </TableHead>
                            <TableHead className="text-zinc-400 text-center">Source - chère</TableHead>
                            <TableHead className="text-zinc-400 text-right">Frais Amazon</TableHead>
                            <TableHead className="text-zinc-400 text-right">Marge nette</TableHead>
                            <TableHead className="text-zinc-400 w-24">Actions</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {products.map((product) => {
                            const amazonMargin = product.amazon_margin_eur ?? product.margin_eur;
                            const amazonMarginPct = product.amazon_margin_percentage ?? product.margin_percentage;
                            const isExpanded = expandedProduct === product.id;
                            
                            return (
                              <>
                                <TableRow 
                                  key={product.id} 
                                  className={`border-zinc-800 cursor-pointer hover:bg-zinc-800/30 transition-colors ${isExpanded ? 'bg-zinc-800/20' : ''}`}
                                  onClick={() => setExpandedProduct(isExpanded ? null : product.id)}
                                >
                                  <TableCell onClick={(e) => e.stopPropagation()}>
                                    <input
                                      type="checkbox"
                                      checked={selectedProducts.includes(product.id)}
                                      onChange={() => toggleProductSelection(product.id)}
                                      className="rounded"
                                    />
                                  </TableCell>
                                  <TableCell>
                                    <div className="max-w-[250px]">
                                      <p className="text-white text-sm font-medium truncate">{product.name}</p>
                                      <p className="text-zinc-500 text-xs">{product.brand} · {product.gtin}</p>
                                    </div>
                                  </TableCell>
                                  <TableCell className="text-right">
                                    <span className="text-white font-semibold text-sm">
                                      {product.supplier_price_eur?.toFixed(2)}€
                                    </span>
                                  </TableCell>
                                  <TableCell className="text-right">
                                    {product.amazon_price_eur ? (
                                      <span className="text-amber-400 font-semibold text-sm">
                                        {product.amazon_price_eur.toFixed(2)}€
                                      </span>
                                    ) : (
                                      <span className="text-zinc-600 text-sm">-</span>
                                    )}
                                  </TableCell>
                                  <TableCell className="text-right">
                                    {product.google_lowest_price_eur ? (
                                      <span className="text-purple-400 font-semibold text-sm">
                                        {product.google_lowest_price_eur.toFixed(2)}€
                                      </span>
                                    ) : product.google_price_eur ? (
                                      <span className="text-purple-400 font-semibold text-sm">
                                        {product.google_price_eur.toFixed(2)}€
                                      </span>
                                    ) : (
                                      <span className="text-zinc-600 text-sm">-</span>
                                    )}
                                  </TableCell>
                                  <TableCell className="text-center">
                                    {getCheapestSourceBadge(product.cheapest_source)}
                                  </TableCell>
                                  <TableCell className="text-right">
                                    {product.amazon_fees_eur ? (
                                      <span className="text-red-400 text-sm">
                                        -{product.amazon_fees_eur.toFixed(2)}€
                                      </span>
                                    ) : (
                                      <span className="text-zinc-600 text-sm">-</span>
                                    )}
                                  </TableCell>
                                  <TableCell className="text-right">
                                    {amazonMargin !== null && amazonMargin !== undefined ? (
                                      <div className="flex flex-col items-end gap-1">
                                        <span className={`font-bold text-sm ${amazonMargin >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                                          {amazonMargin >= 0 ? '+' : ''}{amazonMargin?.toFixed(2)}€
                                        </span>
                                        {getMarginBadge(amazonMargin, amazonMarginPct)}
                                      </div>
                                    ) : (
                                      <Badge variant="secondary" className="text-xs">-</Badge>
                                    )}
                                  </TableCell>
                                  <TableCell onClick={(e) => e.stopPropagation()}>
                                    <div className="flex items-center gap-1">
                                      <Button
                                        size="sm"
                                        onClick={() => handleCompareProduct(product.id)}
                                        disabled={comparing}
                                        className="bg-blue-500/20 border border-blue-500/30 text-blue-400 hover:bg-blue-500/30 h-8 px-2"
                                      >
                                        {comparing && expandedProduct === product.id ? (
                                          <Loader2 className="w-3 h-3 animate-spin" />
                                        ) : (
                                          <RefreshCw className="w-3 h-3" />
                                        )}
                                      </Button>
                                      <Button
                                        size="sm"
                                        onClick={() => setExpandedProduct(isExpanded ? null : product.id)}
                                        variant="ghost"
                                        className="text-zinc-400 h-8 px-2"
                                      >
                                        {isExpanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                                      </Button>
                                    </div>
                                  </TableCell>
                                </TableRow>
                                
                                {/* Expanded Detail Row */}
                                {isExpanded && product.last_compared_at && (
                                  <TableRow key={`${product.id}-detail`} className="border-zinc-800 bg-zinc-900/50">
                                    <TableCell colSpan={9} className="p-0">
                                      <ProductComparisonDetail product={product} compareResult={compareResult} />
                                    </TableCell>
                                  </TableRow>
                                )}
                              </>
                            );
                          })}
                        </TableBody>
                      </Table>
                    </div>

                    {/* Pagination */}
                    <div className="flex items-center justify-between mt-4">
                      <p className="text-zinc-400 text-sm">
                        {currentPage * pageSize + 1} à{" "}
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

/* ==================== PRODUCT COMPARISON DETAIL ==================== */
const ProductComparisonDetail = ({ product, compareResult }) => {
  const supplierPrice = product.supplier_price_eur;
  const amazonPrice = product.amazon_price_eur;
  const googlePrice = product.google_lowest_price_eur || product.google_price_eur;
  const amazonFees = product.amazon_fees_eur;
  const supplierMargin = product.supplier_margin_eur;
  const supplierMarginPct = product.supplier_margin_percentage;
  const googleMargin = product.google_margin_eur;
  const googleMarginPct = product.google_margin_percentage;
  const cheapestSource = product.cheapest_source;
  const bestMargin = product.amazon_margin_eur ?? product.margin_eur;
  const bestMarginPct = product.amazon_margin_percentage ?? product.margin_percentage;

  return (
    <div className="p-6 space-y-6">
      {/* Price Comparison Visual */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Supplier Price Card */}
        <div className={`rounded-lg p-4 border ${cheapestSource === 'supplier' ? 'bg-blue-500/10 border-blue-500/30' : 'bg-zinc-800/50 border-zinc-700'}`}>
          <div className="flex items-center gap-2 mb-3">
            <Store className="w-5 h-5 text-blue-400" />
            <h4 className="text-white font-semibold text-sm">Prix Fournisseur</h4>
            {cheapestSource === 'supplier' && (
              <Badge className="bg-blue-500/30 text-blue-300 text-[10px] ml-auto">LE - CHER</Badge>
            )}
          </div>
          <p className="text-3xl font-bold text-white">{supplierPrice?.toFixed(2)}€</p>
          <p className="text-zinc-500 text-xs mt-1">
            ({product.supplier_price_gbp?.toFixed(2)} £)
          </p>
          {amazonPrice && (
            <div className="mt-3 pt-3 border-t border-zinc-700/50">
              <p className="text-zinc-400 text-xs">Marge si achat fournisseur :</p>
              <p className={`text-lg font-bold ${supplierMargin >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                {supplierMargin >= 0 ? '+' : ''}{supplierMargin?.toFixed(2)}€
                <span className="text-sm font-normal ml-1">({supplierMarginPct?.toFixed(1)}%)</span>
              </p>
            </div>
          )}
        </div>

        {/* Amazon Price Card (Selling price) */}
        <div className="rounded-lg p-4 border bg-amber-500/10 border-amber-500/30">
          <div className="flex items-center gap-2 mb-3">
            <ShoppingCart className="w-5 h-5 text-amber-400" />
            <h4 className="text-white font-semibold text-sm">Prix Amazon (Vente)</h4>
          </div>
          <p className="text-3xl font-bold text-amber-400">{amazonPrice ? `${amazonPrice.toFixed(2)}€` : <span className="text-zinc-500 text-lg">Non trouvé</span>}</p>
          <p className="text-zinc-500 text-xs mt-1">Prix de vente sur Amazon</p>
          {amazonFees && (
            <div className="mt-3 pt-3 border-t border-zinc-700/50">
              <p className="text-zinc-400 text-xs">Frais Amazon (15% TTC) :</p>
              <p className="text-red-400 text-lg font-bold">-{amazonFees?.toFixed(2)}€</p>
            </div>
          )}
        </div>

        {/* Google Price Card */}
        <div className={`rounded-lg p-4 border ${cheapestSource === 'google' ? 'bg-purple-500/10 border-purple-500/30' : 'bg-zinc-800/50 border-zinc-700'}`}>
          <div className="flex items-center gap-2 mb-3">
            <Globe className="w-5 h-5 text-purple-400" />
            <h4 className="text-white font-semibold text-sm">Prix Google (+ bas)</h4>
            {cheapestSource === 'google' && (
              <Badge className="bg-purple-500/30 text-purple-300 text-[10px] ml-auto">LE - CHER</Badge>
            )}
          </div>
          <p className="text-3xl font-bold text-white">{googlePrice?.toFixed(2)}€</p>
          <p className="text-zinc-500 text-xs mt-1">Prix le + bas trouvé en ligne</p>
          {amazonPrice && googlePrice && (
            <div className="mt-3 pt-3 border-t border-zinc-700/50">
              <p className="text-zinc-400 text-xs">Marge si achat Google :</p>
              <p className={`text-lg font-bold ${googleMargin >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                {googleMargin >= 0 ? '+' : ''}{googleMargin?.toFixed(2)}€
                <span className="text-sm font-normal ml-1">({googleMarginPct?.toFixed(1)}%)</span>
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Comparison Summary */}
      {amazonPrice && (
        <div className="bg-zinc-800/30 rounded-lg p-4 border border-zinc-700">
          <h4 className="text-white font-semibold mb-4 flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-lime-400" />
            Résumé de la comparaison
          </h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Fournisseur vs Google */}
            <div className="space-y-2">
              <p className="text-zinc-400 text-sm font-medium">Fournisseur vs Google :</p>
              <div className="flex items-center gap-3">
                <div className="flex items-center gap-2">
                  <Store className="w-4 h-4 text-blue-400" />
                  <span className="text-white">{supplierPrice?.toFixed(2)}€</span>
                </div>
                <span className="text-zinc-500">vs</span>
                <div className="flex items-center gap-2">
                  <Globe className="w-4 h-4 text-purple-400" />
                  <span className="text-white">{googlePrice?.toFixed(2)}€</span>
                </div>
                <ArrowRight className="w-4 h-4 text-zinc-500" />
                {supplierPrice <= googlePrice ? (
                  <Badge className="bg-blue-500/20 text-blue-400 border border-blue-500/30">
                    Fournisseur - cher ({(googlePrice - supplierPrice).toFixed(2)}€)
                  </Badge>
                ) : (
                  <Badge className="bg-purple-500/20 text-purple-400 border border-purple-500/30">
                    Google - cher ({(supplierPrice - googlePrice).toFixed(2)}€)
                  </Badge>
                )}
              </div>
            </div>

            {/* Meilleure marge Amazon */}
            <div className="space-y-2">
              <p className="text-zinc-400 text-sm font-medium">Meilleure marge (revente Amazon) :</p>
              <div className="flex items-center gap-3">
                <div className={`px-4 py-2 rounded-lg ${bestMargin >= 0 ? 'bg-green-500/10 border border-green-500/30' : 'bg-red-500/10 border border-red-500/30'}`}>
                  <p className={`text-2xl font-bold ${bestMargin >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                    {bestMargin >= 0 ? '+' : ''}{bestMargin?.toFixed(2)}€
                  </p>
                  <p className="text-zinc-400 text-xs">
                    {bestMarginPct?.toFixed(1)}% marge nette
                    {cheapestSource && ` (via ${cheapestSource === 'supplier' ? 'fournisseur' : 'Google'})`}
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Calculation breakdown */}
          <div className="mt-4 pt-4 border-t border-zinc-700/50">
            <p className="text-zinc-500 text-xs">
              Calcul : {amazonPrice?.toFixed(2)}€ (Amazon) - {(product.cheapest_buy_price_eur || Math.min(supplierPrice, googlePrice || supplierPrice))?.toFixed(2)}€ (achat) - {amazonFees?.toFixed(2)}€ (frais 15%) = <strong className={bestMargin >= 0 ? 'text-green-400' : 'text-red-400'}>{bestMargin?.toFixed(2)}€</strong>
            </p>
          </div>
        </div>
      )}
    </div>
  );
};

/* ==================== OPPORTUNITIES TAB ==================== */
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
          <CardTitle className="text-white">Meilleures opportunités de revente Amazon</CardTitle>
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
              Comparez d'abord les prix de vos produits dans l'onglet Produits
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {opportunities.map((product, index) => {
              const amazonMargin = product.amazon_margin_eur ?? product.margin_eur;
              const amazonMarginPct = product.amazon_margin_percentage ?? product.margin_percentage;
              const supplierMargin = product.supplier_margin_eur;
              const googleMargin = product.google_margin_eur;
              const cheapestSource = product.cheapest_source;
              const googlePrice = product.google_lowest_price_eur || product.google_price_eur;

              return (
                <div
                  key={product.id}
                  className="bg-zinc-800/50 rounded-lg p-6 border border-zinc-700 hover:border-zinc-600 transition-colors"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-4">
                        <span className="text-2xl font-bold text-zinc-500">
                          #{index + 1}
                        </span>
                        <div>
                          <h3 className="text-white font-semibold">{product.name}</h3>
                          <p className="text-zinc-400 text-sm">
                            {product.brand} · {product.category} · EAN: {product.gtin}
                          </p>
                        </div>
                        {cheapestSource && (
                          <div className="ml-auto">
                            {cheapestSource === 'supplier' ? (
                              <Badge className="bg-blue-500/20 text-blue-400 border border-blue-500/30">
                                <Store className="w-3 h-3 mr-1" />Acheter via Fournisseur
                              </Badge>
                            ) : (
                              <Badge className="bg-purple-500/20 text-purple-400 border border-purple-500/30">
                                <Globe className="w-3 h-3 mr-1" />Acheter via Google
                              </Badge>
                            )}
                          </div>
                        )}
                      </div>

                      <div className="grid grid-cols-2 md:grid-cols-6 gap-4">
                        <div>
                          <p className="text-zinc-500 text-xs mb-1 flex items-center gap-1">
                            <Store className="w-3 h-3" /> Fournisseur
                          </p>
                          <p className="text-white font-semibold">
                            {product.supplier_price_eur?.toFixed(2)}€
                          </p>
                        </div>
                        <div>
                          <p className="text-zinc-500 text-xs mb-1 flex items-center gap-1">
                            <ShoppingCart className="w-3 h-3" /> Amazon (vente)
                          </p>
                          <p className="text-amber-400 font-semibold">
                            {product.amazon_price_eur?.toFixed(2)}€
                          </p>
                        </div>
                        <div>
                          <p className="text-zinc-500 text-xs mb-1 flex items-center gap-1">
                            <Globe className="w-3 h-3" /> Google (+ bas)
                          </p>
                          <p className="text-purple-400 font-semibold">
                            {googlePrice?.toFixed(2)}€
                          </p>
                        </div>
                        <div>
                          <p className="text-zinc-500 text-xs mb-1">Frais Amazon (15%)</p>
                          <p className="text-red-400 font-semibold">
                            -{product.amazon_fees_eur?.toFixed(2)}€
                          </p>
                        </div>
                        <div>
                          <p className="text-zinc-500 text-xs mb-1">Marge fournisseur</p>
                          <p className={`font-semibold ${supplierMargin >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                            {supplierMargin !== null && supplierMargin !== undefined ? `${supplierMargin >= 0 ? '+' : ''}${supplierMargin?.toFixed(2)}€` : '-'}
                          </p>
                        </div>
                        <div>
                          <p className="text-zinc-500 text-xs mb-1">Marge nette</p>
                          <p className={`text-2xl font-bold ${amazonMargin >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                            {amazonMargin >= 0 ? '+' : ''}{amazonMargin?.toFixed(2)}€
                          </p>
                          <Badge className={`mt-1 ${amazonMarginPct >= 0 ? 'bg-green-500/20 text-green-400 border-green-500/30' : 'bg-red-500/20 text-red-400 border-red-500/30'} border`}>
                            {amazonMarginPct >= 0 ? '+' : ''}{amazonMarginPct?.toFixed(1)}%
                          </Badge>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default Catalog;
