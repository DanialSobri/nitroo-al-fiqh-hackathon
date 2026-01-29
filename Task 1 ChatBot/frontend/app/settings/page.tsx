'use client';

import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import { Sidebar, ChatHistory } from '@/components/sidebar/sidebar';
import { SidebarToggle } from '@/components/sidebar/sidebar-toggle';
import { ThemeToggle } from '@/components/theme-toggle';
import { Sparkles, Save, Trash2, Download, Upload, RotateCcw } from 'lucide-react';
import { useTheme } from '@/components/theme-provider';
import { getApiBaseUrl, getCollections, getRecentConversations } from '@/lib/api';

export default function SettingsPage() {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [chatHistory, setChatHistory] = useState<ChatHistory[]>([]);
  const [availableCollections, setAvailableCollections] = useState<string[]>(['all', 'bnm_pdfs', 'iifa_resolutions', 'sc_resolutions']);
  const [selectedCollections, setSelectedCollections] = useState<string[]>(['all']);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const { theme, setTheme } = useTheme();

  // Settings state
  const [apiUrl, setApiUrl] = useState('');
  const [maxResults, setMaxResults] = useState(5);
  const [minScore, setMinScore] = useState(0.5);
  const [defaultCollections, setDefaultCollections] = useState<string[]>(['all']);

  useEffect(() => {
    // Load settings from localStorage
    const savedApiUrl = getApiBaseUrl();
    const savedMaxResults = parseInt(localStorage.getItem('maxResults') || '5', 10);
    const savedMinScore = parseFloat(localStorage.getItem('minScore') || '0.5');
    const savedDefaultCollections = JSON.parse(localStorage.getItem('defaultCollections') || '["all"]');

    setApiUrl(savedApiUrl);
    setMaxResults(savedMaxResults);
    setMinScore(savedMinScore);
    setDefaultCollections(savedDefaultCollections);

    // Load chat history
    // Get or create user ID
    const getUserId = (): string => {
      let userId = localStorage.getItem('userId');
      if (!userId) {
        userId = `user_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
        localStorage.setItem('userId', userId);
      }
      return userId;
    };

    // Load chat history from backend
    const loadChatHistoryFromBackend = async () => {
      try {
        const userId = getUserId();
        const { sessions } = await getRecentConversations(userId, 20);
        
        const history: ChatHistory[] = sessions.map(session => ({
          id: session.session_id,
          title: session.title,
          timestamp: new Date(session.timestamp).getTime()
        }));
        
        setChatHistory(history);
        localStorage.setItem('chatHistory', JSON.stringify(history));
      } catch (err) {
        console.error('Failed to load chat history from backend:', err);
        // Fallback to local storage
        const savedHistory = localStorage.getItem('chatHistory');
        if (savedHistory) {
          try {
            setChatHistory(JSON.parse(savedHistory));
          } catch (e) {
            console.error('Failed to load local chat history:', e);
          }
        }
      }
    };

    loadChatHistoryFromBackend();

    // Load collections
    const loadCollections = async () => {
      try {
        const cols = await getCollections();
        // Ensure we always have the default collections even if API returns empty or only 'all'
        const defaultCollections = ['all', 'bnm_pdfs', 'iifa_resolutions', 'sc_resolutions'];
        if (cols && cols.length > 0) {
          // Merge API collections with defaults, removing duplicates
          const merged = ['all', ...new Set([...cols.filter(c => c !== 'all'), ...defaultCollections.filter(c => c !== 'all')])];
          setAvailableCollections(merged);
        } else {
          // Fallback to defaults if API returns empty
          setAvailableCollections(defaultCollections);
        }
      } catch (err) {
        console.error('Failed to load collections:', err);
        // Fallback to default collections on error
        setAvailableCollections(['all', 'bnm_pdfs', 'iifa_resolutions', 'sc_resolutions']);
      }
    };
    loadCollections();
  }, []);

  const handleSave = () => {
    setSaving(true);
    localStorage.setItem('apiUrl', apiUrl);
    localStorage.setItem('maxResults', maxResults.toString());
    localStorage.setItem('minScore', minScore.toString());
    localStorage.setItem('defaultCollections', JSON.stringify(defaultCollections));
    
    setTimeout(() => {
      setSaving(false);
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    }, 500);
  };

  const handleClearChatHistory = () => {
    if (confirm('Are you sure you want to clear all chat history? This action cannot be undone.')) {
      localStorage.removeItem('chatHistory');
      // Clear individual chat messages
      const keys = Object.keys(localStorage);
      keys.forEach(key => {
        if (key.startsWith('chat_')) {
          localStorage.removeItem(key);
        }
      });
      setChatHistory([]);
      alert('Chat history cleared successfully');
    }
  };

  const handleExportSettings = () => {
    const settings = {
      apiUrl,
      maxResults,
      minScore,
      defaultCollections,
      theme,
      exportDate: new Date().toISOString()
    };
    const blob = new Blob([JSON.stringify(settings, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `neo-ai-settings-${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const handleImportSettings = () => {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = 'application/json';
    input.onchange = (e) => {
      const file = (e.target as HTMLInputElement).files?.[0];
      if (file) {
        const reader = new FileReader();
        reader.onload = (event) => {
          try {
            const settings = JSON.parse(event.target?.result as string);
            if (settings.apiUrl) setApiUrl(settings.apiUrl);
            if (settings.maxResults) setMaxResults(settings.maxResults);
            if (settings.minScore) setMinScore(settings.minScore);
            if (settings.defaultCollections) setDefaultCollections(settings.defaultCollections);
            if (settings.theme) setTheme(settings.theme);
            alert('Settings imported successfully! Click Save to apply.');
          } catch (err) {
            alert('Failed to import settings: Invalid file format');
          }
        };
        reader.readAsText(file);
      }
    };
    input.click();
  };

  const handleReset = () => {
    if (confirm('Are you sure you want to reset all settings to defaults?')) {
      const defaultUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      setApiUrl(defaultUrl);
      setMaxResults(5);
      setMinScore(0.5);
      setDefaultCollections(['all']);
      setTheme('system');
      localStorage.removeItem('apiUrl');
      localStorage.removeItem('maxResults');
      localStorage.removeItem('minScore');
      localStorage.removeItem('defaultCollections');
      alert('Settings reset to defaults');
    }
  };

  return (
    <div className="flex h-screen bg-background">
      <Sidebar
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        chatHistory={chatHistory}
        selectedChatId={null}
        onSelectChat={(id) => {
          if (id) {
            window.location.href = `/chat?session=${id}`;
          } else {
            window.location.href = '/chat';
          }
        }}
        onNewChat={() => {
          window.location.href = '/chat';
        }}
        collections={availableCollections}
        selectedCollections={selectedCollections}
        onCollectionsChange={setSelectedCollections}
      />

      <div className="flex-1 flex flex-col overflow-hidden">
        <header className="border-b border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
          <div className="px-4 py-4">
            <div className="flex items-center justify-between gap-3">
              <div className="flex items-center gap-3">
                <SidebarToggle onToggle={() => setSidebarOpen(!sidebarOpen)} />
                <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center">
                  <Sparkles className="w-5 h-5 text-primary-foreground" />
                </div>
                <div className="min-w-0 flex-1">
                  <h1 className="text-lg sm:text-xl font-semibold text-foreground truncate">Settings</h1>
                  <p className="text-xs text-muted-foreground hidden sm:block">Configure application preferences</p>
                </div>
              </div>
              <ThemeToggle />
            </div>
          </div>
        </header>

        <ScrollArea className="flex-1">
          <div className="container mx-auto px-4 sm:px-6 py-4 sm:py-8 max-w-4xl">
            <div className="space-y-6">
              {/* API Configuration */}
              <div className="bg-card border border-border rounded-lg p-6">
                <h2 className="text-xl font-semibold text-foreground mb-4">API Configuration</h2>
                <div className="space-y-4">
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-foreground">API Base URL</label>
                    <Input
                      type="url"
                      value={apiUrl}
                      onChange={(e) => setApiUrl(e.target.value)}
                      placeholder="http://localhost:8000"
                    />
                    <p className="text-xs text-muted-foreground">
                      Base URL for the backend API. Changes require page refresh to take effect.
                    </p>
                  </div>
                </div>
              </div>

              {/* Search Settings */}
              <div className="bg-card border border-border rounded-lg p-6">
                <h2 className="text-xl font-semibold text-foreground mb-4">Search Settings</h2>
                <div className="space-y-4">
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-foreground">Maximum Results</label>
                    <Input
                      type="number"
                      min="1"
                      max="20"
                      value={maxResults}
                      onChange={(e) => setMaxResults(parseInt(e.target.value, 10) || 5)}
                    />
                    <p className="text-xs text-muted-foreground">
                      Maximum number of reference documents to return per query (1-20)
                    </p>
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-foreground">Minimum Similarity Score</label>
                    <Input
                      type="number"
                      min="0"
                      max="1"
                      step="0.1"
                      value={minScore}
                      onChange={(e) => setMinScore(parseFloat(e.target.value) || 0.5)}
                    />
                    <p className="text-xs text-muted-foreground">
                      Minimum similarity score threshold (0.0-1.0). Higher values return more relevant but fewer results.
                    </p>
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-foreground">Default Collections</label>
                    <div className="space-y-2">
                      {availableCollections.map((col) => (
                        <label key={col} className="flex items-center space-x-2 cursor-pointer">
                          <input
                            type="checkbox"
                            checked={defaultCollections.includes(col)}
                            onChange={(e) => {
                              if (e.target.checked) {
                                if (col === 'all') {
                                  setDefaultCollections(['all']);
                                } else {
                                  setDefaultCollections(prev => prev.filter(c => c !== 'all').concat(col));
                                }
                              } else {
                                if (col === 'all') {
                                  setDefaultCollections([]);
                                } else {
                                  setDefaultCollections(prev => prev.filter(c => c !== col));
                                }
                              }
                            }}
                            className="rounded border-border"
                          />
                          <span className="text-sm text-foreground">{col === 'all' ? 'All Collections' : col}</span>
                        </label>
                      ))}
                    </div>
                    <p className="text-xs text-muted-foreground">
                      Default collections to search when starting a new chat
                    </p>
                  </div>
                </div>
              </div>

              {/* Data Management */}
              <div className="bg-card border border-border rounded-lg p-6">
                <h2 className="text-xl font-semibold text-foreground mb-4">Data Management</h2>
                <div className="space-y-4">
                  <div className="flex items-center justify-between p-4 border border-border rounded-lg">
                    <div>
                      <h3 className="font-medium text-foreground">Chat History</h3>
                      <p className="text-sm text-muted-foreground">
                        {chatHistory.length} conversation{chatHistory.length !== 1 ? 's' : ''} saved
                      </p>
                    </div>
                    <Button
                      variant="destructive"
                      size="sm"
                      onClick={handleClearChatHistory}
                    >
                      <Trash2 className="w-4 h-4 mr-2" />
                      Clear History
                    </Button>
                  </div>
                </div>
              </div>

              {/* Import/Export */}
              <div className="bg-card border border-border rounded-lg p-6">
                <h2 className="text-xl font-semibold text-foreground mb-4">Import / Export</h2>
                <div className="space-y-4">
                  <div className="flex gap-3">
                    <Button
                      variant="outline"
                      onClick={handleExportSettings}
                      className="flex-1"
                    >
                      <Download className="w-4 h-4 mr-2" />
                      Export Settings
                    </Button>
                    <Button
                      variant="outline"
                      onClick={handleImportSettings}
                      className="flex-1"
                    >
                      <Upload className="w-4 h-4 mr-2" />
                      Import Settings
                    </Button>
                  </div>
                  <p className="text-xs text-muted-foreground">
                    Export your settings to a file or import previously saved settings
                  </p>
                </div>
              </div>

              {/* Actions */}
              <div className="flex gap-3">
                <Button
                  onClick={handleSave}
                  disabled={saving}
                  className="flex-1"
                >
                  {saving ? (
                    <>
                      <RotateCcw className="w-4 h-4 mr-2 animate-spin" />
                      Saving...
                    </>
                  ) : saved ? (
                    <>
                      <Save className="w-4 h-4 mr-2" />
                      Saved!
                    </>
                  ) : (
                    <>
                      <Save className="w-4 h-4 mr-2" />
                      Save Settings
                    </>
                  )}
                </Button>
                <Button
                  variant="outline"
                  onClick={handleReset}
                >
                  <RotateCcw className="w-4 h-4 mr-2" />
                  Reset to Defaults
                </Button>
              </div>
            </div>
          </div>
        </ScrollArea>
      </div>
    </div>
  );
}
