import { useState, useEffect } from "react";
import { api, useAuth } from "../App";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/ui/tabs";
import { Badge } from "../components/ui/badge";
import { 
  Key, User, Shield, Check, X, Loader2, 
  Eye, EyeOff, ExternalLink, AlertCircle, ShoppingCart, Search, ToggleLeft, ToggleRight
} from "lucide-react";
import { toast } from "sonner";

const Settings = () => {
  const { user } = useAuth();
  const [loading, setLoading] = useState(false);
  const [apiKeysLoading, setApiKeysLoading] = useState(true);
  const [toggleLoading, setToggleLoading] = useState(false);
  const [showKeys, setShowKeys] = useState({
    google: false,
    googleCx: false,
    keepa: false,
    dataforseoLogin: false,
    dataforseoPassword: false
  });
  
  const [apiKeys, setApiKeys] = useState({
    google_api_key: "",
    google_search_engine_id: "",
    keepa_api_key: "",
    dataforseo_login: "",
    dataforseo_password: ""
  });

  const [apiKeysStatus, setApiKeysStatus] = useState({
    google_api_key_set: false,
    google_search_engine_id_set: false,
    keepa_api_key_set: false,
    dataforseo_login_set: false,
    dataforseo_password_set: false,
    use_google_shopping: false
  });

  useEffect(() => {
    fetchApiKeysStatus();
  }, []);

  const fetchApiKeysStatus = async () => {
    try {
      const response = await api.get("/settings/api-keys");
      setApiKeysStatus(response.data);
    } catch (error) {
      console.error("Error fetching API keys status:", error);
    } finally {
      setApiKeysLoading(false);
    }
  };

  const handleSaveApiKeys = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const response = await api.put("/settings/api-keys", apiKeys);
      setApiKeysStatus(response.data);
      setApiKeys({
        google_api_key: "",
        google_search_engine_id: "",
        keepa_api_key: "",
        dataforseo_login: "",
        dataforseo_password: ""
      });
      toast.success("Clés API mises à jour !");
    } catch (error) {
      toast.error("Erreur lors de la sauvegarde");
    } finally {
      setLoading(false);
    }
  };

  const handleClearKey = async (keyName) => {
    if (!confirm(`Supprimer cette clé API ?`)) return;
    setLoading(true);
    try {
      const payload = { [keyName]: "" };
      const response = await api.put("/settings/api-keys", payload);
      setApiKeysStatus(response.data);
      toast.success("Clé API supprimée !");
    } catch (error) {
      toast.error("Erreur lors de la suppression");
    } finally {
      setLoading(false);
    }
  };

  const handleToggleSearchMode = async () => {
    setToggleLoading(true);
    try {
      const response = await api.put("/settings/google-search-mode");
      setApiKeysStatus(prev => ({
        ...prev,
        use_google_shopping: response.data.use_google_shopping
      }));
      toast.success(response.data.message);
    } catch (error) {
      toast.error("Erreur lors du changement de mode");
    } finally {
      setToggleLoading(false);
    }
  };

  const ApiKeyField = ({ 
    id, 
    label, 
    description, 
    docsUrl, 
    value, 
    onChange, 
    isSet, 
    showKey, 
    onToggleShow,
    keyName,
    inputType = "password"
  }) => (
    <div className="space-y-3 p-4 bg-zinc-800/30 rounded-lg border border-zinc-800">
      <div className="flex items-center justify-between">
        <div>
          <Label htmlFor={id} className="text-zinc-200 font-medium">{label}</Label>
          <p className="text-xs text-zinc-500 mt-1">{description}</p>
        </div>
        <Badge 
          variant="outline" 
          className={isSet ? "border-lime-500/50 text-lime-400" : "border-zinc-700 text-zinc-500"}
        >
          {isSet ? (
            <><Check className="w-3 h-3 mr-1" /> Configurée</>
          ) : (
            <><X className="w-3 h-3 mr-1" /> Non configurée</>
          )}
        </Badge>
      </div>
      
      <div className="flex gap-2">
        <div className="relative flex-1">
          <Input
            id={id}
            data-testid={`${id}-input`}
            type={showKey ? "text" : inputType}
            value={value}
            onChange={onChange}
            className="bg-zinc-950 border-zinc-700 focus:border-lime-500/50 pr-10"
            placeholder={isSet ? "••••••••••••••••" : "Entrez votre clé API"}
          />
          <button
            type="button"
            onClick={onToggleShow}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-500 hover:text-zinc-300"
          >
            {showKey ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
          </button>
        </div>
        {isSet && (
          <Button
            type="button"
            variant="outline"
            onClick={() => handleClearKey(keyName)}
            className="border-red-500/30 text-red-400 hover:bg-red-500/10"
          >
            <X className="w-4 h-4" />
          </Button>
        )}
      </div>

      {docsUrl && (
        <a 
          href={docsUrl} 
          target="_blank" 
          rel="noopener noreferrer"
          className="inline-flex items-center gap-1 text-xs text-zinc-500 hover:text-lime-400 transition-colors"
        >
          <ExternalLink className="w-3 h-3" />
          Documentation
        </a>
      )}
    </div>
  );

  const isGoogleSearchReady = apiKeysStatus.google_api_key_set && apiKeysStatus.google_search_engine_id_set;
  const isGoogleShoppingReady = apiKeysStatus.dataforseo_login_set && apiKeysStatus.dataforseo_password_set;

  return (
    <div className="min-h-screen bg-zinc-950 pt-20 pb-12">
      <div className="max-w-4xl mx-auto px-6">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl md:text-4xl font-bold text-zinc-50 font-['Chivo'] mb-2">
            Paramètres
          </h1>
          <p className="text-zinc-400">
            Gérez votre compte et vos clés API
          </p>
        </div>

        <Tabs defaultValue="api-keys" className="space-y-6">
          <TabsList className="bg-zinc-900 border border-zinc-800">
            <TabsTrigger 
              value="api-keys" 
              data-testid="api-keys-tab"
              className="data-[state=active]:bg-zinc-800 data-[state=active]:text-white"
            >
              <Key className="w-4 h-4 mr-2" />
              Clés API
            </TabsTrigger>
            <TabsTrigger 
              value="profile" 
              data-testid="profile-tab"
              className="data-[state=active]:bg-zinc-800 data-[state=active]:text-white"
            >
              <User className="w-4 h-4 mr-2" />
              Profil
            </TabsTrigger>
          </TabsList>

          {/* API Keys Tab */}
          <TabsContent value="api-keys">
            <Card className="bg-zinc-900 border-zinc-800">
              <CardHeader>
                <CardTitle className="text-zinc-50 flex items-center gap-2">
                  <Key className="w-5 h-5 text-lime-400" />
                  Configuration des clés API
                </CardTitle>
                <CardDescription className="text-zinc-400">
                  Ajoutez vos clés API pour activer les fonctionnalités de recherche avancées.
                  Les fonctionnalités sont mockées si les clés ne sont pas configurées.
                </CardDescription>
              </CardHeader>
              <CardContent>
                {/* Info Banner */}
                <div className="mb-6 p-4 bg-blue-500/10 border border-blue-500/20 rounded-lg flex items-start gap-3">
                  <AlertCircle className="w-5 h-5 text-blue-400 flex-shrink-0 mt-0.5" />
                  <div className="text-sm text-zinc-300">
                    <p className="font-medium text-blue-400 mb-1">Mode démonstration actif</p>
                    <p className="text-zinc-400">
                      Sans clés API, l'application utilise des données de démonstration. 
                      Ajoutez vos clés pour utiliser les vraies APIs Google et Keepa.
                    </p>
                  </div>
                </div>

                {/* ============ Google Search Mode Toggle ============ */}
                <div className="mb-6 p-5 bg-gradient-to-r from-indigo-500/10 to-purple-500/10 border border-indigo-500/20 rounded-xl">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-lg bg-indigo-500/20 flex items-center justify-center">
                        {apiKeysStatus.use_google_shopping ? (
                          <ShoppingCart className="w-5 h-5 text-indigo-400" />
                        ) : (
                          <Search className="w-5 h-5 text-blue-400" />
                        )}
                      </div>
                      <div>
                        <h3 className="text-white font-semibold text-base">Mode de recherche prix</h3>
                        <p className="text-zinc-400 text-xs mt-0.5">
                          Choisissez entre Google Custom Search et Google Shopping
                        </p>
                      </div>
                    </div>
                    <button
                      onClick={handleToggleSearchMode}
                      disabled={toggleLoading}
                      className="flex items-center gap-2 transition-all"
                    >
                      {toggleLoading ? (
                        <Loader2 className="w-5 h-5 animate-spin text-indigo-400" />
                      ) : apiKeysStatus.use_google_shopping ? (
                        <ToggleRight className="w-10 h-10 text-indigo-400 cursor-pointer hover:text-indigo-300 transition-colors" />
                      ) : (
                        <ToggleLeft className="w-10 h-10 text-zinc-500 cursor-pointer hover:text-zinc-400 transition-colors" />
                      )}
                    </button>
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    {/* Google Search Card */}
                    <div className={`p-3 rounded-lg border-2 transition-all ${
                      !apiKeysStatus.use_google_shopping
                        ? 'border-blue-500/50 bg-blue-500/10 shadow-lg shadow-blue-500/10'
                        : 'border-zinc-700/50 bg-zinc-800/30 opacity-60'
                    }`}>
                      <div className="flex items-center gap-2 mb-1">
                        <Search className="w-4 h-4 text-blue-400" />
                        <span className="text-white text-sm font-semibold">Google Search</span>
                        {!apiKeysStatus.use_google_shopping && (
                          <Badge className="bg-blue-500/20 text-blue-300 text-[10px] px-1.5 py-0">ACTIF</Badge>
                        )}
                      </div>
                      <p className="text-zinc-400 text-xs">Recherche web classique via Custom Search API</p>
                      <div className="mt-1.5">
                        <Badge variant="outline" className={`text-[10px] ${isGoogleSearchReady ? 'border-lime-500/40 text-lime-400' : 'border-zinc-700 text-zinc-500'}`}>
                          {isGoogleSearchReady ? '✓ Clés configurées' : '✗ Clés manquantes'}
                        </Badge>
                      </div>
                    </div>

                    {/* Google Shopping Card */}
                    <div className={`p-3 rounded-lg border-2 transition-all ${
                      apiKeysStatus.use_google_shopping
                        ? 'border-indigo-500/50 bg-indigo-500/10 shadow-lg shadow-indigo-500/10'
                        : 'border-zinc-700/50 bg-zinc-800/30 opacity-60'
                    }`}>
                      <div className="flex items-center gap-2 mb-1">
                        <ShoppingCart className="w-4 h-4 text-indigo-400" />
                        <span className="text-white text-sm font-semibold">Google Shopping</span>
                        {apiKeysStatus.use_google_shopping && (
                          <Badge className="bg-indigo-500/20 text-indigo-300 text-[10px] px-1.5 py-0">ACTIF</Badge>
                        )}
                      </div>
                      <p className="text-zinc-400 text-xs">Prix marchands via DataForSEO API</p>
                      <div className="mt-1.5">
                        <Badge variant="outline" className={`text-[10px] ${isGoogleShoppingReady ? 'border-lime-500/40 text-lime-400' : 'border-zinc-700 text-zinc-500'}`}>
                          {isGoogleShoppingReady ? '✓ Identifiants configurés' : '✗ Identifiants manquants'}
                        </Badge>
                      </div>
                    </div>
                  </div>

                  {apiKeysStatus.use_google_shopping && !isGoogleShoppingReady && (
                    <div className="mt-3 p-2 bg-amber-500/10 border border-amber-500/20 rounded-lg flex items-center gap-2">
                      <AlertCircle className="w-4 h-4 text-amber-400 flex-shrink-0" />
                      <p className="text-amber-300 text-xs">
                        Google Shopping activé mais identifiants DataForSEO non configurés. Ajoutez-les ci-dessous.
                      </p>
                    </div>
                  )}
                </div>

                {apiKeysLoading ? (
                  <div className="flex items-center justify-center py-8">
                    <Loader2 className="w-6 h-6 animate-spin text-lime-400" />
                  </div>
                ) : (
                  <form onSubmit={handleSaveApiKeys} className="space-y-6">
                    {/* Google API Key */}
                    <div className={`space-y-4 transition-opacity ${apiKeysStatus.use_google_shopping ? 'opacity-50' : ''}`}>
                      <h3 className="text-lg font-semibold text-zinc-50 flex items-center gap-2">
                        <img src="https://www.google.com/favicon.ico" alt="Google" className="w-4 h-4" />
                        Google Cloud APIs
                        {apiKeysStatus.use_google_shopping && (
                          <Badge className="bg-zinc-700 text-zinc-400 text-[10px]">Désactivé — Google Shopping actif</Badge>
                        )}
                      </h3>
                      
                      <ApiKeyField
                        id="google-api-key"
                        label="Google API Key"
                        description="Pour la recherche par image (Vision API) et la recherche web (Custom Search API)"
                        docsUrl="https://console.cloud.google.com/apis/credentials"
                        value={apiKeys.google_api_key}
                        onChange={(e) => setApiKeys({ ...apiKeys, google_api_key: e.target.value })}
                        isSet={apiKeysStatus.google_api_key_set}
                        showKey={showKeys.google}
                        onToggleShow={() => setShowKeys({ ...showKeys, google: !showKeys.google })}
                        keyName="google_api_key"
                      />

                      <ApiKeyField
                        id="google-cx"
                        label="Custom Search Engine ID"
                        description="L'ID de votre moteur de recherche personnalisé Google"
                        docsUrl="https://programmablesearchengine.google.com/"
                        value={apiKeys.google_search_engine_id}
                        onChange={(e) => setApiKeys({ ...apiKeys, google_search_engine_id: e.target.value })}
                        isSet={apiKeysStatus.google_search_engine_id_set}
                        showKey={showKeys.googleCx}
                        onToggleShow={() => setShowKeys({ ...showKeys, googleCx: !showKeys.googleCx })}
                        keyName="google_search_engine_id"
                      />
                    </div>

                    {/* DataForSEO API (Google Shopping) */}
                    <div className={`space-y-4 transition-opacity ${!apiKeysStatus.use_google_shopping ? 'opacity-50' : ''}`}>
                      <h3 className="text-lg font-semibold text-zinc-50 flex items-center gap-2">
                        <ShoppingCart className="w-5 h-5 text-indigo-400" />
                        DataForSEO — Google Shopping
                        {!apiKeysStatus.use_google_shopping && (
                          <Badge className="bg-zinc-700 text-zinc-400 text-[10px]">Désactivé — Google Search actif</Badge>
                        )}
                      </h3>
                      <p className="text-zinc-500 text-xs -mt-2">
                        Accédez aux prix des marchands Google Shopping. Créez un compte sur{' '}
                        <a href="https://app.dataforseo.com/register" target="_blank" rel="noopener noreferrer" className="text-indigo-400 hover:text-indigo-300 underline">
                          dataforseo.com
                        </a>
                      </p>
                      
                      <ApiKeyField
                        id="dataforseo-login"
                        label="DataForSEO Login"
                        description="Email / login de votre compte DataForSEO"
                        docsUrl="https://app.dataforseo.com/api-access"
                        value={apiKeys.dataforseo_login}
                        onChange={(e) => setApiKeys({ ...apiKeys, dataforseo_login: e.target.value })}
                        isSet={apiKeysStatus.dataforseo_login_set}
                        showKey={showKeys.dataforseoLogin}
                        onToggleShow={() => setShowKeys({ ...showKeys, dataforseoLogin: !showKeys.dataforseoLogin })}
                        keyName="dataforseo_login"
                        inputType="text"
                      />

                      <ApiKeyField
                        id="dataforseo-password"
                        label="DataForSEO Password"
                        description="Mot de passe API de votre compte DataForSEO"
                        docsUrl="https://app.dataforseo.com/api-access"
                        value={apiKeys.dataforseo_password}
                        onChange={(e) => setApiKeys({ ...apiKeys, dataforseo_password: e.target.value })}
                        isSet={apiKeysStatus.dataforseo_password_set}
                        showKey={showKeys.dataforseoPassword}
                        onToggleShow={() => setShowKeys({ ...showKeys, dataforseoPassword: !showKeys.dataforseoPassword })}
                        keyName="dataforseo_password"
                      />
                    </div>

                    {/* Keepa API Key */}
                    <div className="space-y-4">
                      <h3 className="text-lg font-semibold text-zinc-50 flex items-center gap-2">
                        <div className="w-4 h-4 rounded bg-orange-500 flex items-center justify-center text-[8px] font-bold text-white">K</div>
                        Keepa API
                      </h3>
                      
                      <ApiKeyField
                        id="keepa-api-key"
                        label="Keepa API Key"
                        description="Pour le suivi des prix Amazon et l'historique des prix"
                        docsUrl="https://keepa.com/#!api"
                        value={apiKeys.keepa_api_key}
                        onChange={(e) => setApiKeys({ ...apiKeys, keepa_api_key: e.target.value })}
                        isSet={apiKeysStatus.keepa_api_key_set}
                        showKey={showKeys.keepa}
                        onToggleShow={() => setShowKeys({ ...showKeys, keepa: !showKeys.keepa })}
                        keyName="keepa_api_key"
                      />
                    </div>

                    <Button
                      type="submit"
                      data-testid="save-api-keys-btn"
                      disabled={loading || (!apiKeys.google_api_key && !apiKeys.google_search_engine_id && !apiKeys.keepa_api_key && !apiKeys.dataforseo_login && !apiKeys.dataforseo_password)}
                      className="w-full bg-lime-400 text-zinc-950 hover:bg-lime-500 font-bold shadow-[0_0_20px_rgba(163,230,53,0.2)]"
                    >
                      {loading ? (
                        <Loader2 className="w-4 h-4 animate-spin mr-2" />
                      ) : (
                        <Check className="w-4 h-4 mr-2" />
                      )}
                      Sauvegarder les clés
                    </Button>
                  </form>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Profile Tab */}
          <TabsContent value="profile">
            <Card className="bg-zinc-900 border-zinc-800">
              <CardHeader>
                <CardTitle className="text-zinc-50 flex items-center gap-2">
                  <User className="w-5 h-5 text-lime-400" />
                  Informations du profil
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="flex items-center gap-4 p-4 bg-zinc-800/30 rounded-lg border border-zinc-800">
                  <div className="w-16 h-16 rounded-full bg-lime-400/20 flex items-center justify-center">
                    <User className="w-8 h-8 text-lime-400" />
                  </div>
                  <div>
                    <h3 className="text-lg font-bold text-zinc-50">{user?.name}</h3>
                    <p className="text-zinc-400">{user?.email}</p>
                  </div>
                </div>

                <div className="space-y-4">
                  <div className="space-y-2">
                    <Label className="text-zinc-300">Nom</Label>
                    <Input
                      value={user?.name || ""}
                      disabled
                      className="bg-zinc-950 border-zinc-800 text-zinc-400"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label className="text-zinc-300">Email</Label>
                    <Input
                      value={user?.email || ""}
                      disabled
                      className="bg-zinc-950 border-zinc-800 text-zinc-400"
                    />
                  </div>
                </div>

                <div className="p-4 bg-zinc-800/30 rounded-lg border border-zinc-800">
                  <div className="flex items-center gap-3 mb-2">
                    <Shield className="w-5 h-5 text-lime-400" />
                    <span className="text-zinc-200 font-medium">Sécurité</span>
                  </div>
                  <p className="text-sm text-zinc-400">
                    Vos données sont sécurisées et chiffrées. Les clés API sont stockées de manière sécurisée.
                  </p>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

export default Settings;
