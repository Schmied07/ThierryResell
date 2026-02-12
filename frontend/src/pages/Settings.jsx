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
  Eye, EyeOff, ExternalLink, AlertCircle
} from "lucide-react";
import { toast } from "sonner";

const Settings = () => {
  const { user } = useAuth();
  const [loading, setLoading] = useState(false);
  const [apiKeysLoading, setApiKeysLoading] = useState(true);
  const [showKeys, setShowKeys] = useState({
    google: false,
    googleCx: false,
    keepa: false
  });
  
  const [apiKeys, setApiKeys] = useState({
    google_api_key: "",
    google_search_engine_id: "",
    keepa_api_key: ""
  });

  const [apiKeysStatus, setApiKeysStatus] = useState({
    google_api_key_set: false,
    google_search_engine_id_set: false,
    keepa_api_key_set: false
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
        keepa_api_key: ""
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
    keyName 
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
            type={showKey ? "text" : "password"}
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

                {apiKeysLoading ? (
                  <div className="flex items-center justify-center py-8">
                    <Loader2 className="w-6 h-6 animate-spin text-lime-400" />
                  </div>
                ) : (
                  <form onSubmit={handleSaveApiKeys} className="space-y-6">
                    {/* Google API Key */}
                    <div className="space-y-4">
                      <h3 className="text-lg font-semibold text-zinc-50 flex items-center gap-2">
                        <img src="https://www.google.com/favicon.ico" alt="Google" className="w-4 h-4" />
                        Google Cloud APIs
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
                      disabled={loading || (!apiKeys.google_api_key && !apiKeys.google_search_engine_id && !apiKeys.keepa_api_key)}
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
