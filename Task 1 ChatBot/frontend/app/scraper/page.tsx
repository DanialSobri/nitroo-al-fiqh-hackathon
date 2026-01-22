'use client';

import { useState, useEffect } from 'react';
import { 
  getScraperStatus, 
  startScraperJob, 
  getScraperSources,
  addScraperSource,
  updateScraperSource,
  deleteScraperSource,
  getCollections,
  ScraperStatus, 
  ScraperJobRequest,
  ScraperSource,
  ScraperSourceRequest
} from '@/lib/api';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Input } from '@/components/ui/input';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { 
  Play, 
  Loader2, 
  CheckCircle, 
  XCircle, 
  Clock, 
  Database,
  FileText,
  Globe,
  Building2,
  Plus,
  Trash2,
  ExternalLink,
  Edit
} from 'lucide-react';
import { Sidebar, ChatHistory } from '@/components/sidebar/sidebar';
import { SidebarToggle } from '@/components/sidebar/sidebar-toggle';
import { ThemeToggle } from '@/components/theme-toggle';
import { Sparkles } from 'lucide-react';
import { cn } from '@/lib/utils';

export default function ScraperPage() {
  const [status, setStatus] = useState<ScraperStatus | null>(null);
  const [sources, setSources] = useState<ScraperSource[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [chatHistory, setChatHistory] = useState<ChatHistory[]>([]);
  const [availableCollections, setAvailableCollections] = useState<string[]>(['all']);
  const [selectedCollections, setSelectedCollections] = useState<string[]>(['all']);
  const [addSourceOpen, setAddSourceOpen] = useState(false);
  const [editingSourceId, setEditingSourceId] = useState<string | null>(null);
  const [newSource, setNewSource] = useState<ScraperSourceRequest>({
    name: '',
    url: '',
    collection_name: '',
    output_dir: '',
    scraping_strategy: 'direct_links',
    form_selector: '',
    form_button_selector: ''
  });
  const [addingSource, setAddingSource] = useState(false);

  useEffect(() => {
    loadStatus();
    loadSources();
    loadCollections();
    const interval = setInterval(loadStatus, 2000); // Poll every 2 seconds
    
    // Load chat history
    const savedHistory = localStorage.getItem('chatHistory');
    if (savedHistory) {
      try {
        setChatHistory(JSON.parse(savedHistory));
      } catch (e) {
        console.error('Failed to load chat history:', e);
      }
    }
    
    return () => clearInterval(interval);
  }, []);

  const loadStatus = async () => {
    try {
      const data = await getScraperStatus();
      setStatus(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load scraper status');
      console.error('Error loading scraper status:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadSources = async () => {
    try {
      const data = await getScraperSources();
      console.log('Loaded sources:', data.length, data.map(s => s.id));
      setSources(data);
    } catch (err) {
      console.error('Error loading scraper sources:', err);
    }
  };

  const loadCollections = async () => {
    try {
      const cols = await getCollections();
      setAvailableCollections(['all', ...cols]);
    } catch (err) {
      console.error('Failed to load collections:', err);
    }
  };

  const handleStartScraper = async (sourceId: string) => {
    try {
      setError(null);
      await startScraperJob({ source: sourceId as any, use_selenium: false });
      // Status will update via polling
      await loadStatus(); // Refresh immediately
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start scraper');
      console.error('Error starting scraper:', err);
    }
  };

  const handleAddSource = async () => {
    if (!newSource.name || !newSource.url || !newSource.collection_name) {
      setError('Please fill in all required fields');
      return;
    }

    if (newSource.scraping_strategy === 'form_based' && !newSource.form_selector) {
      setError('Form selector is required for form-based scraping');
      return;
    }

    try {
      setAddingSource(true);
      setError(null);
      
      if (editingSourceId) {
        // Update existing source
        await updateScraperSource(editingSourceId, newSource);
      } else {
        // Add new source
        await addScraperSource(newSource);
      }
      
      setAddSourceOpen(false);
      setEditingSourceId(null);
      setNewSource({ 
        name: '', 
        url: '', 
        collection_name: '', 
        output_dir: '',
        scraping_strategy: 'direct_links',
        form_selector: '',
        form_button_selector: ''
      });
      await loadSources();
    } catch (err) {
      setError(err instanceof Error ? err.message : editingSourceId ? 'Failed to update source' : 'Failed to add source');
      console.error('Error saving source:', err);
    } finally {
      setAddingSource(false);
    }
  };

  const handleEditSource = (source: ScraperSource) => {
    setEditingSourceId(source.id);
    setNewSource({
      name: source.name,
      url: source.url,
      collection_name: source.collection_name,
      output_dir: source.output_dir || '',
      scraping_strategy: source.scraping_strategy || 'direct_links',
      form_selector: source.form_selector || '',
      form_button_selector: source.form_button_selector || ''
    });
    setAddSourceOpen(true);
  };

  const handleCancelEdit = () => {
    setAddSourceOpen(false);
    setEditingSourceId(null);
    setNewSource({ 
      name: '', 
      url: '', 
      collection_name: '', 
      output_dir: '',
      scraping_strategy: 'direct_links',
      form_selector: '',
      form_button_selector: ''
    });
  };

  const handleDeleteSource = async (sourceId: string) => {
    if (!confirm(`Are you sure you want to delete this source? This action cannot be undone.`)) {
      return;
    }

    try {
      setError(null);
      await deleteScraperSource(sourceId);
      await loadSources();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete source');
      console.error('Error deleting source:', err);
    }
  };

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return 'Never';
    try {
      return new Date(dateStr).toLocaleString();
    } catch {
      return dateStr;
    }
  };

  const getSourceIcon = (sourceId: string) => {
    switch (sourceId) {
      case 'bnm':
        return <Building2 className="w-5 h-5" />;
      case 'iifa':
        return <Globe className="w-5 h-5" />;
      case 'sc':
        return <FileText className="w-5 h-5" />;
      default:
        return <Database className="w-5 h-5" />;
    }
  };

  const getSourceName = (sourceId: string, sourceName?: string) => {
    if (sourceName) return sourceName;
    switch (sourceId) {
      case 'bnm':
        return 'Bank Negara Malaysia';
      case 'iifa':
        return 'IIFA Resolutions';
      case 'sc':
        return 'Securities Commission';
      case 'all':
        return 'All Sources';
      default:
        return sourceId;
    }
  };

  if (loading && !status) {
    return (
      <div className="flex items-center justify-center h-screen">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="flex h-screen bg-background">
      <Sidebar
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        chatHistory={chatHistory}
        selectedChatId={null}
        onSelectChat={() => {}}
        onNewChat={() => {}}
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
                  <h1 className="text-lg sm:text-xl font-semibold text-foreground truncate">Web Scraper</h1>
                  <p className="text-xs text-muted-foreground hidden sm:block">Monitor and execute document scraping</p>
                </div>
              </div>
              <ThemeToggle />
            </div>
          </div>
        </header>

        <ScrollArea className="flex-1">
          <div className="container mx-auto px-4 sm:px-6 py-4 sm:py-8">
            {error && (
              <div className="mb-4 p-4 bg-destructive/10 border border-destructive rounded-lg">
                <p className="text-destructive text-sm">{error}</p>
              </div>
            )}

            {/* Status Card */}
            <div className="bg-card border border-border rounded-lg p-6 mb-6">
              <h2 className="text-xl font-semibold text-foreground mb-4">Scraper Status</h2>
              
              <div className="space-y-4">
                <div className="flex items-center gap-3">
                  {status?.is_running ? (
                    <>
                      <Loader2 className="w-5 h-5 animate-spin text-primary" />
                      <span className="text-foreground font-medium">Running</span>
                    </>
                  ) : status?.error ? (
                    <>
                      <XCircle className="w-5 h-5 text-destructive" />
                      <span className="text-foreground font-medium">Error</span>
                    </>
                  ) : (
                    <>
                      <CheckCircle className="w-5 h-5 text-green-500" />
                      <span className="text-foreground font-medium">Idle</span>
                    </>
                  )}
                </div>

                {status?.is_running && status.current_job && (
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-muted-foreground">Current Job:</span>
                      <span className="text-sm font-medium text-foreground">
                        {getSourceName(status.current_job, sources.find(s => s.id === status.current_job)?.name)}
                      </span>
                    </div>
                    {status.progress !== null && (
                      <div className="space-y-1">
                        <div className="flex items-center justify-between text-xs">
                          <span className="text-muted-foreground">Progress</span>
                          <span className="text-muted-foreground">
                            {Math.round(status.progress * 100)}%
                          </span>
                        </div>
                        <div className="w-full bg-muted rounded-full h-2">
                          <div
                            className="bg-primary h-2 rounded-full transition-all duration-300"
                            style={{ width: `${status.progress * 100}%` }}
                          />
                        </div>
                      </div>
                    )}
                    <p className="text-sm text-muted-foreground">{status.status_message}</p>
                  </div>
                )}

                {status?.error && (
                  <div className="p-3 bg-destructive/10 rounded-lg">
                    <p className="text-sm text-destructive">{status.error}</p>
                  </div>
                )}

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-4 border-t border-border">
                  <div>
                    <p className="text-xs text-muted-foreground mb-1">Last Run</p>
                    <p className="text-sm font-medium text-foreground flex items-center gap-2">
                      <Clock className="w-4 h-4" />
                      {formatDate(status?.last_run || null)}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground mb-1">Last Success</p>
                    <p className="text-sm font-medium text-foreground flex items-center gap-2">
                      <CheckCircle className="w-4 h-4 text-green-500" />
                      {formatDate(status?.last_success || null)}
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* Scraper Actions */}
            <div className="bg-card border border-border rounded-lg p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-semibold text-foreground">Execute Scraper</h2>
                <Dialog open={addSourceOpen} onOpenChange={setAddSourceOpen}>
                  <DialogTrigger asChild>
                    <Button size="sm" variant="outline">
                      <Plus className="w-4 h-4 mr-2" />
                      Add Source
                    </Button>
                  </DialogTrigger>
                  <DialogContent className="p-0">
                    <div className="px-6 pt-6">
                      <DialogHeader>
                        <DialogTitle>{editingSourceId ? 'Edit Scraper Source' : 'Add New Scraper Source'}</DialogTitle>
                        <DialogDescription>
                          {editingSourceId 
                            ? 'Update the scraper source configuration.'
                            : 'Add a new website to scrape PDFs from. The scraper will automatically find and index PDF documents.'}
                        </DialogDescription>
                      </DialogHeader>
                    </div>
                    <div className="space-y-4 px-6 py-4">
                      <div className="space-y-2">
                        <label className="text-sm font-medium text-foreground">Source Name *</label>
                        <Input
                          type="text"
                          value={newSource.name}
                          onChange={(e) => setNewSource({ ...newSource, name: e.target.value })}
                          placeholder="e.g., Islamic Finance Institute"
                        />
                      </div>
                      <div className="space-y-2">
                        <label className="text-sm font-medium text-foreground">Website URL *</label>
                        <Input
                          type="url"
                          value={newSource.url}
                          onChange={(e) => setNewSource({ ...newSource, url: e.target.value })}
                          placeholder="https://example.com/documents"
                        />
                      </div>
                      <div className="space-y-2">
                        <label className="text-sm font-medium text-foreground">Collection Name *</label>
                        <Input
                          type="text"
                          value={newSource.collection_name}
                          onChange={(e) => setNewSource({ ...newSource, collection_name: e.target.value })}
                          placeholder="e.g., custom_documents"
                        />
                        <p className="text-xs text-muted-foreground">
                          This will be the Qdrant collection name (use lowercase, underscores allowed)
                        </p>
                      </div>
                      <div className="space-y-2">
                        <label className="text-sm font-medium text-foreground">Output Directory (Optional)</label>
                        <Input
                          type="text"
                          value={newSource.output_dir || ''}
                          onChange={(e) => setNewSource({ ...newSource, output_dir: e.target.value })}
                          placeholder="pdfs/custom (auto-generated if empty)"
                        />
                      </div>
                      <div className="space-y-2">
                        <label className="text-sm font-medium text-foreground">Scraping Strategy *</label>
                        <select
                          value={newSource.scraping_strategy || 'direct_links'}
                          onChange={(e) => setNewSource({ ...newSource, scraping_strategy: e.target.value })}
                          className="w-full px-3 py-2 border border-border rounded-md bg-background text-foreground"
                        >
                          <option value="direct_links">Direct Links (PDF links directly in HTML)</option>
                          <option value="table_based">Table Based (PDFs in HTML tables)</option>
                          <option value="form_based">Form Based (PDFs via form submission)</option>
                        </select>
                        <p className="text-xs text-muted-foreground">
                          Select how PDFs are accessed on this website
                        </p>
                      </div>
                      {newSource.scraping_strategy === 'form_based' && (
                        <>
                          <div className="space-y-2">
                            <label className="text-sm font-medium text-foreground">Form Selector *</label>
                            <Input
                              type="text"
                              value={newSource.form_selector || ''}
                              onChange={(e) => setNewSource({ ...newSource, form_selector: e.target.value })}
                              placeholder="#download-file or .form-class"
                            />
                            <p className="text-xs text-muted-foreground">
                              CSS selector for the form element (e.g., #download-file, .form-class, or form[id="download-file"])
                            </p>
                          </div>
                          <div className="space-y-2">
                            <label className="text-sm font-medium text-foreground">Form Button Selector (Optional)</label>
                            <Input
                              type="text"
                              value={newSource.form_button_selector || ''}
                              onChange={(e) => setNewSource({ ...newSource, form_button_selector: e.target.value })}
                              placeholder="#muat-turun or button[type='submit']"
                            />
                            <p className="text-xs text-muted-foreground">
                              CSS selector for the submit button (e.g., #muat-turun). If not provided, the form will be submitted directly.
                            </p>
                          </div>
                        </>
                      )}
                    </div>
                    <div className="px-6 pb-6 border-t border-border pt-4">
                      <DialogFooter>
                      <Button
                        variant="outline"
                        onClick={handleCancelEdit}
                      >
                        Cancel
                      </Button>
                      <Button onClick={handleAddSource} disabled={addingSource}>
                        {addingSource ? (
                          <>
                            <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                            {editingSourceId ? 'Updating...' : 'Adding...'}
                          </>
                        ) : (
                          editingSourceId ? 'Update Source' : 'Add Source'
                        )}
                      </Button>
                      </DialogFooter>
                    </div>
                  </DialogContent>
                </Dialog>
              </div>
              
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
                {/* All Sources button */}
                <div className="border border-border rounded-lg p-4 hover:border-primary/50 transition-colors">
                  <div className="flex items-center gap-3 mb-3">
                    <Database className="w-5 h-5" />
                    <h3 className="font-semibold text-foreground">All Sources</h3>
                  </div>
                  <Button
                    onClick={() => handleStartScraper('all')}
                    disabled={status?.is_running || false}
                    className="w-full"
                    size="sm"
                  >
                    {status?.is_running && status.current_job === 'all' ? (
                      <>
                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                        Running...
                      </>
                    ) : (
                      <>
                        <Play className="w-4 h-4 mr-2" />
                        Start All
                      </>
                    )}
                  </Button>
                </div>

                {/* Dynamic sources */}
                {sources.map((source) => (
                  <div
                    key={source.id}
                    className="border border-border rounded-lg p-4 hover:border-primary/50 transition-colors relative group"
                  >
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-3 min-w-0 flex-1">
                        {getSourceIcon(source.id)}
                        <div className="min-w-0 flex-1">
                          <h3 className="font-semibold text-foreground truncate">{source.name}</h3>
                          {source.type === 'custom' && (
                            <span className="text-xs text-muted-foreground">Custom</span>
                          )}
                        </div>
                      </div>
                      {source.type === 'custom' && (
                        <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                          <Button
                            variant="ghost"
                            size="sm"
                            className="h-6 w-6 p-0"
                            onClick={() => handleEditSource(source)}
                            title="Edit source"
                          >
                            <Edit className="w-4 h-4 text-primary" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="h-6 w-6 p-0"
                            onClick={() => handleDeleteSource(source.id)}
                            title="Delete source"
                          >
                            <Trash2 className="w-4 h-4 text-destructive" />
                          </Button>
                        </div>
                      )}
                    </div>
                    {source.url && (
                      <a
                        href={source.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-xs text-muted-foreground hover:text-primary flex items-center gap-1 mb-2 truncate"
                      >
                        <ExternalLink className="w-3 h-3" />
                        <span className="truncate">{source.url}</span>
                      </a>
                    )}
                    <Button
                      onClick={() => handleStartScraper(source.id)}
                      disabled={status?.is_running || false}
                      className="w-full"
                      size="sm"
                    >
                      {status?.is_running && status.current_job === source.id ? (
                        <>
                          <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                          Running...
                        </>
                      ) : (
                        <>
                          <Play className="w-4 h-4 mr-2" />
                          Start Scraping
                        </>
                      )}
                    </Button>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </ScrollArea>
      </div>
    </div>
  );
}
