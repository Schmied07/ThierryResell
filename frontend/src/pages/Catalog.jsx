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
  ArrowRight, Percent, Info, ExternalLink, Tag, TrendingDown,
  Minus, Sparkles, Star, Image, MapPin, Columns, ArrowLeft
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
  
  // Column Mapping state
  const [importStep, setImportStep] = useState(1); // 1=upload, 2=mapping
  const [previewData, setPreviewData] = useState(null); // columns, sample_data, suggested_mapping
  const [columnMapping, setColumnMapping] = useState({});
  const [previewing, setPreviewing] = useState(false);
  const [selectedFileColumn, setSelectedFileColumn] = useState(null); // For visual mapping
  const [selectedAppField, setSelectedAppField] = useState(null); // For visual mapping
  
  // Filters
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedBrand, setSelectedBrand] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("");
  const [minMargin, setMinMargin] = useState("");
  const [comparedOnly, setComparedOnly] = useState(false);
  const [minOpportunityScore, setMinOpportunityScore] = useState("");
  const [opportunityLevel, setOpportunityLevel] = useState("");
  const [trendFilter, setTrendFilter] = useState("");
  
  // Pagination
  const [currentPage, setCurrentPage] = useState(0);
  const [pageSize] = useState(50);
  const [totalProducts, setTotalProducts] = useState(0);
  const [apiKeysConfigured, setApiKeysConfigured] = useState(false);

  useEffect(() => {
    fetchStats();
    fetchProducts();
    fetchApiKeyStatus();
  }, [currentPage, selectedBrand, selectedCategory, minMargin, comparedOnly, searchQuery, minOpportunityScore, opportunityLevel, trendFilter]);

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
      if (minOpportunityScore) params.min_opportunity_score = parseInt(minOpportunityScore);
      if (opportunityLevel) params.opportunity_level = opportunityLevel;
      if (trendFilter) params.trend = trendFilter;

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
        setImportStep(1);
        setPreviewData(null);
        setColumnMapping({});
      } else {
        toast.error("Veuillez sélectionner un fichier Excel (.xlsx ou .xls)");
      }
    }
  };

  const handlePreview = async () => {
    if (!file) {
      toast.error("Veuillez sélectionner un fichier");
      return;
    }

    setPreviewing(true);
    try {
      const formData = new FormData();
      formData.append("file", file);

      const response = await api.post("/catalog/preview", formData, {
        timeout: 60000
      });

      setPreviewData(response.data);
      setColumnMapping(response.data.suggested_mapping || {});
      setImportStep(2);
      toast.success(`${response.data.total_rows} lignes détectées. Vérifiez le mapping des colonnes.`);
    } catch (error) {
      toast.error(error.response?.data?.detail || "Erreur lors de la prévisualisation");
    } finally {
      setPreviewing(false);
    }
  };

  const handleImport = async () => {
    if (!file) {
      toast.error("Veuillez sélectionner un fichier");
      return;
    }

    // Validate required fields are mapped
    const requiredFields = ['GTIN', 'Name', 'Category', 'Brand', 'Price'];
    const missingFields = requiredFields.filter(f => !columnMapping[f]);
    if (missingFields.length > 0) {
      toast.error(`Colonnes requises non mappées : ${missingFields.join(', ')}`);
      return;
    }

    setUploading(true);
    try {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("column_mapping_json", JSON.stringify(columnMapping));

      const response = await api.post("/catalog/import", formData, {
        timeout: 120000
      });

      toast.success(
        `Import réussi ! ${response.data.imported} produits importés, ${response.data.skipped} ignorés`
      );
      
      setFile(null);
      setImportStep(1);
      setPreviewData(null);
      setColumnMapping({});
      if (fileInputRef.current) fileInputRef.current.value = "";
      
      fetchStats();
      fetchProducts();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Erreur lors de l'import");
    } finally {
      setUploading(false);
    }
  };

  const handleMappingChange = (field, value) => {
    setColumnMapping(prev => {
      const newMapping = { ...prev };
      if (value === '') {
        delete newMapping[field];
      } else {
        newMapping[field] = value;
      }
      return newMapping;
    });
  };

  const resetImport = () => {
    setFile(null);
    setImportStep(1);
    setPreviewData(null);
    setColumnMapping({});
    if (fileInputRef.current) fileInputRef.current.value = "";
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

  const [comparingAll, setComparingAll] = useState(false);

  const handleCompareAll = async () => {
    if (!window.confirm(`Rechercher les prix pour TOUS les produits du catalogue (${totalProducts} produits) ? Cette opération peut prendre quelques minutes.`)) {
      return;
    }

    setComparingAll(true);
    try {
      const response = await api.post("/catalog/compare-all", {}, { timeout: 300000 });
      toast.success(
        `Recherche terminée ! ${response.data.success} produits comparés sur ${response.data.total}, ${response.data.failed} erreurs`
      );
      fetchProducts();
      fetchStats();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Erreur lors de la recherche globale");
    } finally {
      setComparingAll(false);
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

  const getTrendIcon = (trend) => {
    if (!trend) return <span className="text-zinc-600 text-sm">-</span>;
    
    if (trend === "hausse") {
      return (
        <div className="flex items-center justify-center gap-1 text-red-400">
          <TrendingUp className="w-4 h-4" />
          <span className="text-xs font-medium">Hausse</span>
        </div>
      );
    } else if (trend === "baisse") {
      return (
        <div className="flex items-center justify-center gap-1 text-green-400">
          <TrendingDown className="w-4 h-4" />
          <span className="text-xs font-medium">Baisse</span>
        </div>
      );
    } else {
      return (
        <div className="flex items-center justify-center gap-1 text-blue-400">
          <Minus className="w-4 h-4" />
          <span className="text-xs font-medium">Stable</span>
        </div>
      );
    }
  };

  const getOpportunityScoreBadge = (score, level) => {
    if (score === null || score === undefined) {
      return <Badge variant="secondary" className="text-xs">-</Badge>;
    }
    
    let bgColor, textColor, borderColor;
    if (level === "Excellent") {
      bgColor = "bg-purple-500/20";
      textColor = "text-purple-300";
      borderColor = "border-purple-500/30";
    } else if (level === "Bon") {
      bgColor = "bg-green-500/20";
      textColor = "text-green-400";
      borderColor = "border-green-500/30";
    } else if (level === "Moyen") {
      bgColor = "bg-yellow-500/20";
      textColor = "text-yellow-400";
      borderColor = "border-yellow-500/30";
    } else {
      bgColor = "bg-gray-500/20";
      textColor = "text-gray-400";
      borderColor = "border-gray-500/30";
    }
    
    return (
      <Badge className={`${bgColor} ${textColor} border ${borderColor} text-xs font-bold flex items-center gap-1`}>
        <Star className="w-3 h-3" />
        {score}/100
      </Badge>
    );
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
                <div className="flex items-center justify-between">
                  <CardTitle className="text-white flex items-center gap-2">
                    {importStep === 1 ? (
                      <><Upload className="w-5 h-5" /> Importer un catalogue Excel</>
                    ) : (
                      <><Columns className="w-5 h-5" /> Mapper les colonnes</>
                    )}
                  </CardTitle>
                  {importStep === 2 && (
                    <div className="flex items-center gap-2">
                      <Badge className="bg-blue-500/20 text-blue-300 border border-blue-500/30">
                        Étape 2/2
                      </Badge>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={resetImport}
                        className="border-zinc-700 text-zinc-300"
                      >
                        <ArrowLeft className="w-4 h-4 mr-1" />
                        Retour
                      </Button>
                    </div>
                  )}
                  {importStep === 1 && file && (
                    <Badge className="bg-blue-500/20 text-blue-300 border border-blue-500/30">
                      Étape 1/2
                    </Badge>
                  )}
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Step 1: File Upload */}
                {importStep === 1 && (
                  <>
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
                          onClick={handlePreview}
                          disabled={previewing}
                          className="bg-gradient-to-r from-blue-500 to-purple-500"
                        >
                          {previewing ? (
                            <>
                              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                              Analyse en cours...
                            </>
                          ) : (
                            <>
                              <Columns className="w-4 h-4 mr-2" />
                              Analyser et mapper les colonnes
                            </>
                          )}
                        </Button>
                      </div>
                    )}

                    <div className="bg-blue-500/10 border border-blue-500/20 rounded-lg p-4">
                      <h4 className="text-blue-400 font-semibold mb-2">Format attendu</h4>
                      <p className="text-zinc-400 text-sm mb-2">
                        Votre fichier Excel peut contenir n'importe quelles colonnes. Vous pourrez les mapper aux champs requis à l'étape suivante.
                      </p>
                      <ul className="text-zinc-400 text-sm space-y-1 list-disc list-inside">
                        <li><strong>GTIN/EAN</strong> - Code-barres du produit (requis)</li>
                        <li><strong>Nom</strong> - Nom du produit (requis)</li>
                        <li><strong>Catégorie</strong> - Catégorie du produit (requis)</li>
                        <li><strong>Marque</strong> - Marque du produit (requis)</li>
                        <li><strong>Prix</strong> - Prix fournisseur (requis)</li>
                        <li><strong className="text-green-400">Image</strong> - URL de l'image du produit (optionnel - permet la recherche Google par image)</li>
                      </ul>
                    </div>
                  </>
                )}

                {/* Step 2: Column Mapping */}
                {importStep === 2 && previewData && (
                  <>
                    {/* Mapping Interface */}
                    <div className="bg-gradient-to-br from-blue-500/5 to-purple-500/5 rounded-lg p-5 border border-blue-500/20">
                      <div className="flex items-center gap-2 mb-4">
                        <MapPin className="w-5 h-5 text-blue-400" />
                        <h4 className="text-white font-semibold">Associer les colonnes du fichier aux champs</h4>
                        <Badge className="bg-zinc-700 text-zinc-300 text-xs">
                          {previewData.total_rows} lignes détectées
                        </Badge>
                      </div>
                      
                      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-4">
                        {/* Required fields */}
                        {['GTIN', 'Name', 'Category', 'Brand', 'Price'].map(field => {
                          const labels = {
                            'GTIN': { label: 'Code EAN / GTIN', icon: '🔢', desc: 'Code-barres du produit' },
                            'Name': { label: 'Nom du produit', icon: '📝', desc: 'Nom/désignation' },
                            'Category': { label: 'Catégorie', icon: '📁', desc: 'Catégorie du produit' },
                            'Brand': { label: 'Marque', icon: '🏷️', desc: 'Marque/fabricant' },
                            'Price': { label: 'Prix fournisseur', icon: '💰', desc: 'Prix en devise source' }
                          };
                          const info = labels[field];
                          const isMapped = !!columnMapping[field];
                          
                          return (
                            <div key={field} className={`rounded-lg p-3 border ${isMapped ? 'bg-green-500/5 border-green-500/30' : 'bg-red-500/5 border-red-500/30'}`}>
                              <div className="flex items-center gap-2 mb-2">
                                <span className="text-lg">{info.icon}</span>
                                <div>
                                  <p className="text-white text-sm font-semibold">{info.label} <span className="text-red-400">*</span></p>
                                  <p className="text-zinc-500 text-xs">{info.desc}</p>
                                </div>
                                {isMapped && <CheckCircle className="w-4 h-4 text-green-400 ml-auto" />}
                              </div>
                              <select
                                value={columnMapping[field] || ''}
                                onChange={(e) => handleMappingChange(field, e.target.value)}
                                className="w-full bg-zinc-800 border border-zinc-700 rounded-md px-3 py-2 text-white text-sm focus:border-blue-500 focus:outline-none"
                              >
                                <option value="">-- Sélectionner une colonne --</option>
                                {previewData.columns.map(col => (
                                  <option key={col} value={col}>{col}</option>
                                ))}
                              </select>
                            </div>
                          );
                        })}
                        
                        {/* Optional Image field */}
                        <div className={`rounded-lg p-3 border ${columnMapping['Image'] ? 'bg-green-500/5 border-green-500/30' : 'bg-zinc-800/30 border-zinc-700'}`}>
                          <div className="flex items-center gap-2 mb-2">
                            <span className="text-lg">🖼️</span>
                            <div>
                              <p className="text-white text-sm font-semibold">Image <span className="text-zinc-500 text-xs font-normal">(optionnel)</span></p>
                              <p className="text-zinc-500 text-xs">URL de l'image - active la recherche Google par image</p>
                            </div>
                            {columnMapping['Image'] && <CheckCircle className="w-4 h-4 text-green-400 ml-auto" />}
                          </div>
                          <select
                            value={columnMapping['Image'] || ''}
                            onChange={(e) => handleMappingChange('Image', e.target.value)}
                            className="w-full bg-zinc-800 border border-zinc-700 rounded-md px-3 py-2 text-white text-sm focus:border-blue-500 focus:outline-none"
                          >
                            <option value="">-- Aucune colonne --</option>
                            {previewData.columns.map(col => (
                              <option key={col} value={col}>{col}</option>
                            ))}
                          </select>
                        </div>
                      </div>
                    </div>

                    {/* Data Preview Table */}
                    <div className="bg-zinc-800/30 rounded-lg border border-zinc-700 overflow-hidden">
                      <div className="flex items-center gap-2 p-3 bg-zinc-800/50 border-b border-zinc-700">
                        <Search className="w-4 h-4 text-zinc-400" />
                        <h4 className="text-zinc-300 font-semibold text-sm">Aperçu des données (5 premières lignes)</h4>
                      </div>
                      <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                          <thead>
                            <tr className="bg-zinc-800/80">
                              {previewData.columns.map(col => {
                                // Check if this column is mapped to any field
                                const mappedField = Object.entries(columnMapping).find(([, v]) => v === col)?.[0];
                                return (
                                  <th key={col} className={`px-3 py-2 text-left text-xs font-medium whitespace-nowrap ${
                                    mappedField ? 'text-green-400 bg-green-500/5' : 'text-zinc-500'
                                  }`}>
                                    {col}
                                    {mappedField && (
                                      <Badge className="ml-1 bg-green-500/20 text-green-300 text-[10px] px-1 py-0">
                                        {mappedField}
                                      </Badge>
                                    )}
                                  </th>
                                );
                              })}
                            </tr>
                          </thead>
                          <tbody>
                            {previewData.sample_data.map((row, idx) => (
                              <tr key={idx} className="border-t border-zinc-700/50">
                                {previewData.columns.map(col => {
                                  const mappedField = Object.entries(columnMapping).find(([, v]) => v === col)?.[0];
                                  const cellValue = row[col];
                                  const isImage = mappedField === 'Image' && cellValue && (cellValue.startsWith('http') || cellValue.startsWith('//'));
                                  return (
                                    <td key={col} className={`px-3 py-2 text-xs whitespace-nowrap ${
                                      mappedField ? 'text-white bg-green-500/5' : 'text-zinc-400'
                                    }`}>
                                      {isImage ? (
                                        <div className="flex items-center gap-2">
                                          <img src={cellValue} alt="" className="w-8 h-8 object-cover rounded" onError={(e) => { e.target.style.display = 'none'; }} />
                                          <span className="truncate max-w-[120px]">{cellValue}</span>
                                        </div>
                                      ) : (
                                        <span className="truncate block max-w-[200px]">{cellValue ?? '-'}</span>
                                      )}
                                    </td>
                                  );
                                })}
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>

                    {/* Import Button */}
                    <div className="flex items-center justify-between pt-2">
                      <div className="flex items-center gap-2 text-zinc-400 text-sm">
                        <Info className="w-4 h-4" />
                        <span>
                          {Object.keys(columnMapping).filter(k => columnMapping[k]).length} colonnes mappées sur {previewData.columns.length} disponibles
                        </span>
                      </div>
                      <Button
                        onClick={handleImport}
                        disabled={uploading || ['GTIN', 'Name', 'Category', 'Brand', 'Price'].some(f => !columnMapping[f])}
                        className="bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 text-white font-semibold px-6 py-2 shadow-lg"
                      >
                        {uploading ? (
                          <>
                            <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                            Import en cours...
                          </>
                        ) : (
                          <>
                            <CheckCircle className="w-4 h-4 mr-2" />
                            Importer {previewData.total_rows} produits
                          </>
                        )}
                      </Button>
                    </div>
                  </>
                )}
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
                    <Button
                      onClick={handleCompareAll}
                      disabled={comparingAll || comparing || totalProducts === 0}
                      className="bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white font-semibold shadow-lg shadow-blue-500/20"
                    >
                      {comparingAll ? (
                        <>
                          <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                          Recherche en cours...
                        </>
                      ) : (
                        <>
                          <Search className="w-4 h-4 mr-2" />
                          Rechercher tous les produits
                        </>
                      )}
                    </Button>
                    {selectedProducts.length > 0 && (
                      <Button
                        onClick={handleCompareBatch}
                        disabled={comparing || comparingAll}
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
                            <TableHead className="text-zinc-400 text-center">
                              <div className="flex items-center justify-center gap-1">
                                <TrendingUp className="w-3 h-3" />
                                Tendance
                              </div>
                            </TableHead>
                            <TableHead className="text-zinc-400 text-center">
                              <div className="flex items-center justify-center gap-1">
                                <Sparkles className="w-3 h-3" />
                                Score
                              </div>
                            </TableHead>
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
                                    <div className="flex items-center gap-3 max-w-[280px]">
                                      {product.image_url ? (
                                        <img 
                                          src={product.image_url} 
                                          alt={product.name}
                                          className="w-10 h-10 object-cover rounded-lg border border-zinc-700 flex-shrink-0"
                                          onError={(e) => { e.target.style.display = 'none'; }}
                                        />
                                      ) : (
                                        <div className="w-10 h-10 bg-zinc-800 rounded-lg border border-zinc-700 flex items-center justify-center flex-shrink-0">
                                          <Package className="w-4 h-4 text-zinc-600" />
                                        </div>
                                      )}
                                      <div className="min-w-0">
                                        <p className="text-white text-sm font-medium truncate">{product.name}</p>
                                        <p className="text-zinc-500 text-xs">{product.brand} · {product.gtin}</p>
                                      </div>
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
                                  <TableCell className="text-center">
                                    {getTrendIcon(product.price_trend?.trend)}
                                  </TableCell>
                                  <TableCell className="text-center">
                                    {getOpportunityScoreBadge(product.opportunity_score, product.opportunity_level)}
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
                                    <TableCell colSpan={11} className="p-0">
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
          <p className="text-3xl font-bold text-white">{googlePrice ? `${googlePrice.toFixed(2)}€` : <span className="text-zinc-500 text-lg">Non trouvé</span>}</p>
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

      {/* Google Suppliers Detail Section */}
      {product.google_suppliers_results && product.google_suppliers_results.length > 0 && (
        <div className="bg-gradient-to-br from-purple-500/5 to-indigo-500/5 rounded-lg p-5 border border-purple-500/20">
          <div className="flex items-center gap-2 mb-4">
            <Globe className="w-5 h-5 text-purple-400" />
            <h4 className="text-white font-semibold">Fournisseurs trouvés par Google</h4>
            <Badge className="bg-purple-500/20 text-purple-300 text-xs">
              {product.google_suppliers_results.length} résultat{product.google_suppliers_results.length > 1 ? 's' : ''}
            </Badge>
            {product.image_url && (
              <Badge className="bg-green-500/20 text-green-300 text-xs border border-green-500/30">
                <Image className="w-3 h-3 mr-1" />
                Recherche image active
              </Badge>
            )}
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {product.google_suppliers_results.map((supplier, idx) => (
              <div 
                key={idx}
                className={`relative rounded-lg p-4 border transition-all hover:shadow-lg ${
                  supplier.is_lowest 
                    ? 'bg-purple-500/10 border-purple-500/40 ring-2 ring-purple-500/30' 
                    : supplier.is_amazon
                    ? 'bg-amber-500/5 border-amber-500/30 hover:border-amber-500/50'
                    : 'bg-zinc-800/50 border-zinc-700 hover:border-purple-500/30'
                }`}
              >
                {supplier.is_lowest && (
                  <div className="absolute -top-2 -right-2">
                    <Badge className="bg-gradient-to-r from-purple-500 to-pink-500 text-white text-[10px] shadow-lg animate-pulse">
                      ⭐ PLUS BAS
                    </Badge>
                  </div>
                )}
                
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center gap-2">
                    {supplier.is_amazon ? (
                      <ShoppingCart className="w-4 h-4 text-amber-400" />
                    ) : (
                      <Store className="w-4 h-4 text-purple-400" />
                    )}
                    <h5 className="text-white font-semibold text-sm truncate max-w-[150px]" title={supplier.supplier_name}>
                      {supplier.supplier_name}
                    </h5>
                    {supplier.is_amazon && (
                      <Badge className="bg-amber-500/20 text-amber-300 text-[10px] px-1.5 py-0 border border-amber-500/30">
                        Amazon
                      </Badge>
                    )}
                  </div>
                  {supplier.is_lowest && (
                    <Tag className="w-4 h-4 text-purple-400 flex-shrink-0" />
                  )}
                </div>
                
                <div className="mb-3">
                  <p className={`text-2xl font-bold ${supplier.is_lowest ? 'text-purple-300' : supplier.is_amazon ? 'text-amber-300' : 'text-white'}`}>
                    {supplier.price.toFixed(2)}€
                  </p>
                </div>
                
                <a
                  href={supplier.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className={`flex items-center justify-center gap-2 w-full px-3 py-2 ${
                    supplier.is_amazon 
                      ? 'bg-amber-500/20 hover:bg-amber-500/30 border-amber-500/40 text-amber-300 hover:text-amber-200'
                      : 'bg-purple-500/20 hover:bg-purple-500/30 border-purple-500/40 text-purple-300 hover:text-purple-200'
                  } border rounded-md text-sm font-medium transition-colors`}
                >
                  <span>Voir le produit</span>
                  <ExternalLink className="w-4 h-4" />
                </a>
              </div>
            ))}
          </div>
          
          <div className="mt-4 pt-4 border-t border-purple-500/20">
            <p className="text-zinc-400 text-xs flex items-center gap-2">
              <Info className="w-4 h-4" />
              Prix le plus bas mis en avant automatiquement. Les résultats Amazon sont identifiés avec un badge 🛒 spécifique.
            </p>
          </div>
        </div>
      )}

      {/* Price Trend Analysis Section */}
      {product.price_trend && (
        <div className="bg-gradient-to-br from-blue-500/5 to-cyan-500/5 rounded-lg p-5 border border-blue-500/20">
          <div className="flex items-center gap-2 mb-4">
            <TrendingUp className="w-5 h-5 text-blue-400" />
            <h4 className="text-white font-semibold">📊 Analyse de Tendances (Keepa)</h4>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Current Trend */}
            <div className="bg-zinc-800/50 rounded-lg p-4 border border-zinc-700">
              <p className="text-zinc-400 text-xs mb-2">Tendance actuelle</p>
              <div className="flex items-center gap-2">
                {product.price_trend.trend === "hausse" && (
                  <>
                    <TrendingUp className="w-6 h-6 text-red-400" />
                    <span className="text-xl font-bold text-red-400">Hausse</span>
                  </>
                )}
                {product.price_trend.trend === "baisse" && (
                  <>
                    <TrendingDown className="w-6 h-6 text-green-400" />
                    <span className="text-xl font-bold text-green-400">Baisse</span>
                  </>
                )}
                {product.price_trend.trend === "stable" && (
                  <>
                    <Minus className="w-6 h-6 text-blue-400" />
                    <span className="text-xl font-bold text-blue-400">Stable</span>
                  </>
                )}
              </div>
              {product.price_trend.is_favorable && (
                <Badge className="bg-green-500/20 text-green-400 border border-green-500/30 text-xs mt-2">
                  ✓ Moment favorable pour vendre
                </Badge>
              )}
            </div>

            {/* Volatility */}
            <div className="bg-zinc-800/50 rounded-lg p-4 border border-zinc-700">
              <p className="text-zinc-400 text-xs mb-2">Volatilité du marché</p>
              <div className="flex items-center gap-3">
                <div className="flex-1">
                  <div className="w-full bg-zinc-700 rounded-full h-3 overflow-hidden">
                    <div 
                      className={`h-full rounded-full transition-all ${
                        product.price_trend.volatility < 10 ? 'bg-green-500' :
                        product.price_trend.volatility < 20 ? 'bg-blue-500' :
                        product.price_trend.volatility < 30 ? 'bg-yellow-500' : 'bg-red-500'
                      }`}
                      style={{ width: `${Math.min(product.price_trend.volatility, 100)}%` }}
                    ></div>
                  </div>
                </div>
                <span className="text-white font-bold">{product.price_trend.volatility?.toFixed(1)}%</span>
              </div>
              <p className="text-zinc-500 text-xs mt-1">
                {product.price_trend.volatility < 10 && "Très stable"}
                {product.price_trend.volatility >= 10 && product.price_trend.volatility < 20 && "Stable"}
                {product.price_trend.volatility >= 20 && product.price_trend.volatility < 30 && "Modéré"}
                {product.price_trend.volatility >= 30 && "Très volatile"}
              </p>
            </div>

            {/* Price Averages */}
            <div className="bg-zinc-800/50 rounded-lg p-4 border border-zinc-700">
              <p className="text-zinc-400 text-xs mb-3">Prix moyens historiques</p>
              <div className="space-y-2">
                {product.price_trend.avg_30d && (
                  <div className="flex justify-between items-center">
                    <span className="text-zinc-400 text-sm">30 jours :</span>
                    <span className="text-white font-semibold">{product.price_trend.avg_30d.toFixed(2)}€</span>
                  </div>
                )}
                {product.price_trend.avg_60d && (
                  <div className="flex justify-between items-center">
                    <span className="text-zinc-400 text-sm">60 jours :</span>
                    <span className="text-white font-semibold">{product.price_trend.avg_60d.toFixed(2)}€</span>
                  </div>
                )}
                {product.price_trend.avg_90d && (
                  <div className="flex justify-between items-center">
                    <span className="text-zinc-400 text-sm">90 jours :</span>
                    <span className="text-white font-semibold">{product.price_trend.avg_90d.toFixed(2)}€</span>
                  </div>
                )}
              </div>
            </div>

            {/* Min/Max Range */}
            <div className="bg-zinc-800/50 rounded-lg p-4 border border-zinc-700">
              <p className="text-zinc-400 text-xs mb-3">Fourchette (30 jours)</p>
              <div className="space-y-2">
                {product.price_trend.min_30d && (
                  <div className="flex justify-between items-center">
                    <span className="text-zinc-400 text-sm">Minimum :</span>
                    <span className="text-green-400 font-semibold">{product.price_trend.min_30d.toFixed(2)}€</span>
                  </div>
                )}
                {product.price_trend.max_30d && (
                  <div className="flex justify-between items-center">
                    <span className="text-zinc-400 text-sm">Maximum :</span>
                    <span className="text-red-400 font-semibold">{product.price_trend.max_30d.toFixed(2)}€</span>
                  </div>
                )}
                {product.price_trend.min_30d && product.price_trend.max_30d && (
                  <div className="flex justify-between items-center pt-2 border-t border-zinc-700">
                    <span className="text-zinc-400 text-sm">Écart :</span>
                    <span className="text-white font-semibold">
                      {(product.price_trend.max_30d - product.price_trend.min_30d).toFixed(2)}€
                    </span>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Opportunity Score Section */}
      {product.opportunity_score !== null && product.opportunity_score !== undefined && (
        <div className="bg-gradient-to-br from-purple-500/5 to-pink-500/5 rounded-lg p-5 border border-purple-500/20">
          <div className="flex items-center gap-2 mb-4">
            <Sparkles className="w-5 h-5 text-purple-400" />
            <h4 className="text-white font-semibold">⭐ Score d'Opportunité de Revente</h4>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Score Gauge */}
            <div className="flex items-center justify-center">
              <div className="relative w-40 h-40">
                <svg className="transform -rotate-90 w-40 h-40">
                  <circle
                    cx="80"
                    cy="80"
                    r="70"
                    stroke="currentColor"
                    strokeWidth="12"
                    fill="transparent"
                    className="text-zinc-800"
                  />
                  <circle
                    cx="80"
                    cy="80"
                    r="70"
                    stroke="currentColor"
                    strokeWidth="12"
                    fill="transparent"
                    strokeDasharray={`${2 * Math.PI * 70}`}
                    strokeDashoffset={`${2 * Math.PI * 70 * (1 - product.opportunity_score / 100)}`}
                    className={`${
                      product.opportunity_level === "Excellent" ? 'text-purple-500' :
                      product.opportunity_level === "Bon" ? 'text-green-500' :
                      product.opportunity_level === "Moyen" ? 'text-yellow-500' : 'text-gray-500'
                    }`}
                    strokeLinecap="round"
                  />
                </svg>
                <div className="absolute inset-0 flex flex-col items-center justify-center">
                  <span className={`text-4xl font-bold ${
                    product.opportunity_level === "Excellent" ? 'text-purple-400' :
                    product.opportunity_level === "Bon" ? 'text-green-400' :
                    product.opportunity_level === "Moyen" ? 'text-yellow-400' : 'text-gray-400'
                  }`}>
                    {product.opportunity_score}
                  </span>
                  <span className="text-zinc-500 text-sm">/100</span>
                  <Badge className={`mt-2 ${
                    product.opportunity_level === "Excellent" ? 'bg-purple-500/20 text-purple-300 border-purple-500/30' :
                    product.opportunity_level === "Bon" ? 'bg-green-500/20 text-green-400 border-green-500/30' :
                    product.opportunity_level === "Moyen" ? 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30' :
                    'bg-gray-500/20 text-gray-400 border-gray-500/30'
                  } border text-xs`}>
                    {product.opportunity_level}
                  </Badge>
                </div>
              </div>
            </div>

            {/* Score Breakdown */}
            <div className="space-y-3">
              <p className="text-zinc-400 text-xs mb-3">Détail du calcul (sur 100 points)</p>
              
              {product.opportunity_details && (
                <>
                  <div className="flex items-center justify-between bg-zinc-800/50 rounded p-2 border border-zinc-700">
                    <div className="flex items-center gap-2">
                      <DollarSign className="w-4 h-4 text-green-400" />
                      <span className="text-sm text-zinc-300">Marge</span>
                    </div>
                    <span className="text-white font-bold">{product.opportunity_details.margin_score || 0}/30</span>
                  </div>

                  <div className="flex items-center justify-between bg-zinc-800/50 rounded p-2 border border-zinc-700">
                    <div className="flex items-center gap-2">
                      <TrendingUp className="w-4 h-4 text-blue-400" />
                      <span className="text-sm text-zinc-300">Tendance prix</span>
                    </div>
                    <span className="text-white font-bold">{product.opportunity_details.trend_score || 0}/25</span>
                  </div>

                  <div className="flex items-center justify-between bg-zinc-800/50 rounded p-2 border border-zinc-700">
                    <div className="flex items-center gap-2">
                      <Globe className="w-4 h-4 text-purple-400" />
                      <span className="text-sm text-zinc-300">Concurrence</span>
                    </div>
                    <span className="text-white font-bold">{product.opportunity_details.competition_score || 0}/20</span>
                  </div>

                  <div className="flex items-center justify-between bg-zinc-800/50 rounded p-2 border border-zinc-700">
                    <div className="flex items-center gap-2">
                      <Minus className="w-4 h-4 text-yellow-400" />
                      <span className="text-sm text-zinc-300">Volatilité</span>
                    </div>
                    <span className="text-white font-bold">{product.opportunity_details.volatility_score || 0}/15</span>
                  </div>

                  <div className="flex items-center justify-between bg-zinc-800/50 rounded p-2 border border-zinc-700">
                    <div className="flex items-center gap-2">
                      <Tag className="w-4 h-4 text-amber-400" />
                      <span className="text-sm text-zinc-300">Prix vs historique</span>
                    </div>
                    <span className="text-white font-bold">{product.opportunity_details.position_score || 0}/10</span>
                  </div>
                </>
              )}
            </div>
          </div>

          <div className="mt-4 pt-4 border-t border-purple-500/20">
            <p className="text-zinc-400 text-xs flex items-center gap-2">
              <Info className="w-4 h-4" />
              Le score combine la marge, la tendance des prix Amazon, le nombre de concurrents Google, la volatilité du marché et la position du prix actuel.
            </p>
          </div>
        </div>
      )}

      {/* Profitability Predictions */}
      {product.profitability_predictions && (
        <div className="bg-gradient-to-br from-emerald-900/20 to-teal-900/20 rounded-lg p-4 border border-emerald-500/30">
          <h4 className="text-white font-semibold mb-4 flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-emerald-400" />
            🔮 Prévisions de Profitabilité (30/60/90 jours)
          </h4>

          {/* Recommendation Badge */}
          <div className="mb-4 flex items-center gap-3">
            <div className="flex-1">
              {product.profitability_predictions.recommendation === 'acheter_maintenant' && (
                <Badge className="bg-green-500/20 text-green-300 border border-green-500/30 text-sm px-3 py-1">
                  ✅ Acheter Maintenant - Profit en hausse
                </Badge>
              )}
              {product.profitability_predictions.recommendation === 'attendre' && (
                <Badge className="bg-amber-500/20 text-amber-300 border border-amber-500/30 text-sm px-3 py-1">
                  ⏳ Attendre - Profit stable
                </Badge>
              )}
              {product.profitability_predictions.recommendation === 'risque' && (
                <Badge className="bg-red-500/20 text-red-300 border border-red-500/30 text-sm px-3 py-1">
                  ⚠️ Risqué - Profit en baisse ou volatilité élevée
                </Badge>
              )}
            </div>
            <div className="text-right">
              <p className="text-zinc-400 text-xs">Confiance</p>
              <p className={`text-sm font-bold ${
                product.profitability_predictions.confidence_level === 'high' ? 'text-green-400' : 
                product.profitability_predictions.confidence_level === 'medium' ? 'text-yellow-400' : 
                'text-red-400'
              }`}>
                {product.profitability_predictions.confidence_level === 'high' ? 'Haute' : 
                 product.profitability_predictions.confidence_level === 'medium' ? 'Moyenne' : 
                 'Faible'}
              </p>
            </div>
          </div>

          {/* Predictions Grid */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {/* 30 days */}
            <div className="bg-zinc-800/50 rounded-lg p-3 border border-emerald-500/20">
              <p className="text-emerald-300 text-sm font-semibold mb-2">30 jours</p>
              <div className="space-y-1">
                <div className="flex justify-between items-center">
                  <span className="text-zinc-400 text-xs">Prix prévu</span>
                  <span className="text-white text-sm font-bold">
                    {product.profitability_predictions.predictions['30d'].price.toFixed(2)}€
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-zinc-400 text-xs">Profit prévu</span>
                  <span className={`text-sm font-bold ${
                    product.profitability_predictions.predictions['30d'].profit_eur >= 0 ? 'text-green-400' : 'text-red-400'
                  }`}>
                    {product.profitability_predictions.predictions['30d'].profit_eur >= 0 ? '+' : ''}
                    {product.profitability_predictions.predictions['30d'].profit_eur.toFixed(2)}€
                  </span>
                </div>
                <div className="flex justify-between items-center pt-1 border-t border-zinc-700">
                  <span className="text-zinc-400 text-xs">Changement</span>
                  <span className={`text-xs font-bold ${
                    product.profitability_predictions.predictions['30d'].profit_change_pct >= 0 ? 'text-green-400' : 'text-red-400'
                  }`}>
                    {product.profitability_predictions.predictions['30d'].profit_change_pct >= 0 ? '+' : ''}
                    {product.profitability_predictions.predictions['30d'].profit_change_pct}%
                  </span>
                </div>
              </div>
            </div>

            {/* 60 days */}
            <div className="bg-zinc-800/50 rounded-lg p-3 border border-emerald-500/20">
              <p className="text-emerald-300 text-sm font-semibold mb-2">60 jours</p>
              <div className="space-y-1">
                <div className="flex justify-between items-center">
                  <span className="text-zinc-400 text-xs">Prix prévu</span>
                  <span className="text-white text-sm font-bold">
                    {product.profitability_predictions.predictions['60d'].price.toFixed(2)}€
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-zinc-400 text-xs">Profit prévu</span>
                  <span className={`text-sm font-bold ${
                    product.profitability_predictions.predictions['60d'].profit_eur >= 0 ? 'text-green-400' : 'text-red-400'
                  }`}>
                    {product.profitability_predictions.predictions['60d'].profit_eur >= 0 ? '+' : ''}
                    {product.profitability_predictions.predictions['60d'].profit_eur.toFixed(2)}€
                  </span>
                </div>
                <div className="flex justify-between items-center pt-1 border-t border-zinc-700">
                  <span className="text-zinc-400 text-xs">Changement</span>
                  <span className={`text-xs font-bold ${
                    product.profitability_predictions.predictions['60d'].profit_change_pct >= 0 ? 'text-green-400' : 'text-red-400'
                  }`}>
                    {product.profitability_predictions.predictions['60d'].profit_change_pct >= 0 ? '+' : ''}
                    {product.profitability_predictions.predictions['60d'].profit_change_pct}%
                  </span>
                </div>
              </div>
            </div>

            {/* 90 days */}
            <div className="bg-zinc-800/50 rounded-lg p-3 border border-emerald-500/20">
              <p className="text-emerald-300 text-sm font-semibold mb-2">90 jours</p>
              <div className="space-y-1">
                <div className="flex justify-between items-center">
                  <span className="text-zinc-400 text-xs">Prix prévu</span>
                  <span className="text-white text-sm font-bold">
                    {product.profitability_predictions.predictions['90d'].price.toFixed(2)}€
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-zinc-400 text-xs">Profit prévu</span>
                  <span className={`text-sm font-bold ${
                    product.profitability_predictions.predictions['90d'].profit_eur >= 0 ? 'text-green-400' : 'text-red-400'
                  }`}>
                    {product.profitability_predictions.predictions['90d'].profit_eur >= 0 ? '+' : ''}
                    {product.profitability_predictions.predictions['90d'].profit_eur.toFixed(2)}€
                  </span>
                </div>
                <div className="flex justify-between items-center pt-1 border-t border-zinc-700">
                  <span className="text-zinc-400 text-xs">Changement</span>
                  <span className={`text-xs font-bold ${
                    product.profitability_predictions.predictions['90d'].profit_change_pct >= 0 ? 'text-green-400' : 'text-red-400'
                  }`}>
                    {product.profitability_predictions.predictions['90d'].profit_change_pct >= 0 ? '+' : ''}
                    {product.profitability_predictions.predictions['90d'].profit_change_pct}%
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Risk Assessment */}
          <div className="mt-3 pt-3 border-t border-emerald-500/20 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-zinc-400" />
              <span className="text-zinc-400 text-xs">Risque de volatilité:</span>
              <Badge className={`text-xs ${
                product.profitability_predictions.volatility_risk === 'faible' ? 'bg-green-500/20 text-green-300 border-green-500/30' :
                product.profitability_predictions.volatility_risk === 'moyen' ? 'bg-yellow-500/20 text-yellow-300 border-yellow-500/30' :
                'bg-red-500/20 text-red-300 border-red-500/30'
              } border`}>
                {product.profitability_predictions.volatility_risk === 'faible' ? 'Faible' :
                 product.profitability_predictions.volatility_risk === 'moyen' ? 'Moyen' : 'Élevé'}
              </Badge>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-zinc-400 text-xs">Tendance:</span>
              <span className={`text-xs font-bold ${
                product.profitability_predictions.trend_direction === 'hausse' ? 'text-green-400' :
                product.profitability_predictions.trend_direction === 'baisse' ? 'text-red-400' :
                'text-zinc-400'
              }`}>
                {product.profitability_predictions.trend_direction === 'hausse' ? '📈 Hausse' :
                 product.profitability_predictions.trend_direction === 'baisse' ? '📉 Baisse' : '➡️ Stable'}
              </span>
            </div>
          </div>

          <div className="mt-3 pt-3 border-t border-emerald-500/20">
            <p className="text-zinc-400 text-xs flex items-center gap-2">
              <Info className="w-4 h-4" />
              Prévisions basées sur l'historique de prix Keepa (régression linéaire). Plus la volatilité est faible et les données historiques abondantes, plus la prévision est fiable.
            </p>
          </div>
        </div>
      )}

      {/* Multi-Market Arbitrage */}
      {product.multi_market_arbitrage && product.multi_market_arbitrage.analysis_available && (
        <div className="bg-gradient-to-br from-indigo-900/20 to-purple-900/20 rounded-lg p-4 border border-indigo-500/30">
          <h4 className="text-white font-semibold mb-4 flex items-center gap-2">
            <Globe className="w-5 h-5 text-indigo-400" />
            🌍 Arbitrage Multi-Marchés Amazon (FR/UK/DE/ES)
          </h4>

          {/* Best Opportunities Summary */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mb-4">
            <div className="bg-green-500/10 rounded-lg p-3 border border-green-500/30">
              <p className="text-green-300 text-xs font-medium mb-2">💰 Meilleur marché VENTE</p>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="text-2xl">{product.multi_market_arbitrage.best_sell_market.flag}</span>
                  <span className="text-white font-bold">{product.multi_market_arbitrage.best_sell_market.country}</span>
                </div>
                <span className="text-green-400 font-bold text-lg">
                  +{product.multi_market_arbitrage.best_sell_market.margin_eur.toFixed(2)}€
                </span>
              </div>
            </div>

            <div className="bg-blue-500/10 rounded-lg p-3 border border-blue-500/30">
              <p className="text-blue-300 text-xs font-medium mb-2">🛒 Meilleur marché ACHAT</p>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="text-2xl">{product.multi_market_arbitrage.best_buy_market.flag}</span>
                  <span className="text-white font-bold">{product.multi_market_arbitrage.best_buy_market.country}</span>
                </div>
                <span className="text-blue-400 font-bold text-lg">
                  {product.multi_market_arbitrage.best_buy_market.price_eur.toFixed(2)}€
                </span>
              </div>
            </div>
          </div>

          {/* Arbitrage Opportunity */}
          {product.multi_market_arbitrage.arbitrage_opportunity_eur > 0 && (
            <div className="bg-purple-500/10 rounded-lg p-3 border border-purple-500/30 mb-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Sparkles className="w-5 h-5 text-purple-400" />
                  <span className="text-white font-semibold">Opportunité d'arbitrage international</span>
                </div>
                <span className="text-purple-400 font-bold text-xl">
                  +{product.multi_market_arbitrage.arbitrage_opportunity_eur.toFixed(2)}€
                </span>
              </div>
              <p className="text-zinc-400 text-xs mt-2">
                Profit supplémentaire en vendant sur le meilleur marché vs le marché de référence
              </p>
            </div>
          )}

          {/* Markets Comparison Table */}
          <div className="bg-zinc-800/30 rounded-lg p-3 border border-zinc-700">
            <p className="text-zinc-300 text-sm font-semibold mb-3">Comparaison par marché</p>
            <div className="space-y-2">
              {Object.entries(product.multi_market_arbitrage.markets).map(([code, market]) => (
                <div key={code} className="flex items-center justify-between bg-zinc-800/50 rounded p-2">
                  <div className="flex items-center gap-3 flex-1">
                    <span className="text-2xl">{market.flag}</span>
                    <div className="flex-1">
                      <p className="text-white text-sm font-medium">{market.country}</p>
                      {market.available ? (
                        <p className="text-zinc-400 text-xs">
                          {market.price_local.toFixed(2)} {market.currency}
                          {market.exchange_rate !== 1.0 && ` (${market.price_eur.toFixed(2)}€)`}
                        </p>
                      ) : (
                        <p className="text-red-400 text-xs">{market.reason || 'Non disponible'}</p>
                      )}
                    </div>
                  </div>
                  {market.available && (
                    <div className="text-right">
                      <p className={`text-sm font-bold ${market.margin_eur >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                        {market.margin_eur >= 0 ? '+' : ''}{market.margin_eur.toFixed(2)}€
                      </p>
                      <p className="text-zinc-500 text-xs">{market.margin_percentage.toFixed(1)}%</p>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>

          <div className="mt-3 pt-3 border-t border-indigo-500/20">
            <p className="text-zinc-400 text-xs flex items-center gap-2">
              <Info className="w-4 h-4" />
              Analyse des prix Amazon sur 4 marchés européens. Les prix sont convertis en EUR. Frais Amazon: 15% par marché.
            </p>
          </div>
        </div>
      )}

      {/* Comparison Summary */}
      {amazonPrice && (
        <div className="bg-zinc-800/30 rounded-lg p-4 border border-zinc-700">
          <h4 className="text-white font-semibold mb-4 flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-lime-400" />
            Résumé de la comparaison
          </h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Fournisseur vs Google */}
            {googlePrice ? (
              <div className="space-y-2">
                <p className="text-zinc-400 text-sm font-medium">Fournisseur vs Google :</p>
                <div className="flex items-center gap-3 flex-wrap">
                  <div className="flex items-center gap-2">
                    <Store className="w-4 h-4 text-blue-400" />
                    <span className="text-white">{supplierPrice?.toFixed(2)}€</span>
                  </div>
                  <span className="text-zinc-500">vs</span>
                  <div className="flex items-center gap-2">
                    <Globe className="w-4 h-4 text-purple-400" />
                    <span className="text-white">{googlePrice.toFixed(2)}€</span>
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
            ) : (
              <div className="space-y-2">
                <p className="text-zinc-400 text-sm font-medium">Fournisseur vs Google :</p>
                <p className="text-zinc-500 text-sm">Prix Google non trouvé pour ce produit</p>
              </div>
            )}

            {/* Meilleure marge Amazon */}
            <div className="space-y-2">
              <p className="text-zinc-400 text-sm font-medium">Meilleure marge (revente Amazon) :</p>
              {bestMargin != null ? (
                <div className="flex items-center gap-3">
                  <div className={`px-4 py-2 rounded-lg ${bestMargin >= 0 ? 'bg-green-500/10 border border-green-500/30' : 'bg-red-500/10 border border-red-500/30'}`}>
                    <p className={`text-2xl font-bold ${bestMargin >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                      {bestMargin >= 0 ? '+' : ''}{bestMargin.toFixed(2)}€
                    </p>
                    <p className="text-zinc-400 text-xs">
                      {bestMarginPct?.toFixed(1)}% marge nette
                      {cheapestSource && ` (via ${cheapestSource === 'supplier' ? 'fournisseur' : 'Google'})`}
                    </p>
                  </div>
                </div>
              ) : (
                <p className="text-zinc-500 text-sm">Impossible de calculer (données manquantes)</p>
              )}
            </div>
          </div>

          {/* Calculation breakdown */}
          {bestMargin != null && (
            <div className="mt-4 pt-4 border-t border-zinc-700/50">
              <p className="text-zinc-500 text-xs">
                Calcul : {amazonPrice?.toFixed(2)}€ (Amazon) - {(product.cheapest_buy_price_eur || supplierPrice)?.toFixed(2)}€ (achat) - {amazonFees?.toFixed(2)}€ (frais 15%) = <strong className={bestMargin >= 0 ? 'text-green-400' : 'text-red-400'}>{bestMargin.toFixed(2)}€</strong>
              </p>
            </div>
          )}
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
