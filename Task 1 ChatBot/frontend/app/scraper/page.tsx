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
  getScraperSchedules,
  createScraperSchedule,
  updateScraperSchedule,
  deleteScraperSchedule,
  ScraperStatus, 
  ScraperJobRequest,
  ScraperSource,
  ScraperSourceRequest,
  ScraperSchedule,
  ScraperScheduleRequest
} from '@/lib/api';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Input } from '@/components/ui/input';
import { Checkbox } from '@/components/ui/checkbox';
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
  Edit,
  Calendar,
  Power,
  PowerOff
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
  const [availableCollections, setAvailableCollections] = useState<string[]>(['all', 'bnm_pdfs', 'iifa_resolutions', 'sc_resolutions']);
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
  const [schedules, setSchedules] = useState<ScraperSchedule[]>([]);
  const [scheduleDialogOpen, setScheduleDialogOpen] = useState(false);
  const [editingScheduleId, setEditingScheduleId] = useState<string | null>(null);
  const [newSchedule, setNewSchedule] = useState<ScraperScheduleRequest>({
    name: '',
    source: 'all',
    schedule_type: 'interval',
    enabled: true,
    interval_value: 6,
    interval_unit: 'hours'
  });
  const [addingSchedule, setAddingSchedule] = useState(false);

  useEffect(() => {
    loadStatus();
    loadSources();
    loadCollections();
    loadSchedules();
    const interval = setInterval(loadStatus, 2000); // Poll every 2 seconds
    
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

  const loadSchedules = async () => {
    try {
      const data = await getScraperSchedules();
      setSchedules(data);
    } catch (err) {
      console.error('Error loading schedules:', err);
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
      
      // Reload sources to ensure schedule dialog has latest data
      await loadSources();
      // Also reload collections in case a new collection was created
      await loadCollections();
      
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
      // Reload sources to ensure schedule dialog has latest data
      await loadSources();
      // Also reload schedules in case any schedules were using this source
      await loadSchedules();
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
                  <DialogContent className="p-0 max-w-2xl">
                    <div className="px-6 pt-6 pb-4">
                      <DialogHeader>
                        <div className="flex items-center gap-3 mb-2">
                          <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
                            <Globe className="w-5 h-5 text-primary" />
                          </div>
                          <div className="flex-1">
                            <DialogTitle className="text-xl">{editingSourceId ? 'Edit Scraper Source' : 'Add New Scraper Source'}</DialogTitle>
                            <DialogDescription className="mt-1.5">
                              {editingSourceId 
                                ? 'Update the scraper source configuration.'
                                : 'Add a new website to scrape PDFs from. The scraper will automatically find and index PDF documents.'}
                            </DialogDescription>
                          </div>
                        </div>
                      </DialogHeader>
                    </div>
                    <div className="px-6 py-4 space-y-5 max-h-[60vh] overflow-y-auto scrollbar-hide">
                      <div className="space-y-2">
                        <label className="text-sm font-semibold text-foreground flex items-center gap-2">
                          <FileText className="w-4 h-4 text-muted-foreground" />
                          Source Name <span className="text-destructive">*</span>
                        </label>
                        <Input
                          type="text"
                          value={newSource.name}
                          onChange={(e) => setNewSource({ ...newSource, name: e.target.value })}
                          placeholder="e.g., Islamic Finance Institute"
                          className="h-10"
                        />
                      </div>
                      <div className="space-y-2">
                        <label className="text-sm font-semibold text-foreground flex items-center gap-2">
                          <Globe className="w-4 h-4 text-muted-foreground" />
                          Website URL <span className="text-destructive">*</span>
                        </label>
                        <Input
                          type="url"
                          value={newSource.url}
                          onChange={(e) => setNewSource({ ...newSource, url: e.target.value })}
                          placeholder="https://example.com/documents"
                          className="h-10"
                        />
                      </div>
                      <div className="space-y-2">
                        <label className="text-sm font-semibold text-foreground flex items-center gap-2">
                          <Database className="w-4 h-4 text-muted-foreground" />
                          Collection Name <span className="text-destructive">*</span>
                        </label>
                        <Input
                          type="text"
                          value={newSource.collection_name}
                          onChange={(e) => setNewSource({ ...newSource, collection_name: e.target.value })}
                          placeholder="e.g., custom_documents"
                          className="h-10"
                        />
                        <p className="text-xs text-muted-foreground pl-6">
                          This will be the Qdrant collection name (use lowercase, underscores allowed)
                        </p>
                      </div>
                      <div className="space-y-2">
                        <label className="text-sm font-semibold text-foreground flex items-center gap-2">
                          <FileText className="w-4 h-4 text-muted-foreground" />
                          Output Directory <span className="text-xs text-muted-foreground font-normal">(Optional)</span>
                        </label>
                        <Input
                          type="text"
                          value={newSource.output_dir || ''}
                          onChange={(e) => setNewSource({ ...newSource, output_dir: e.target.value })}
                          placeholder="pdfs/custom (auto-generated if empty)"
                          className="h-10"
                        />
                      </div>
                      <div className="space-y-2">
                        <label className="text-sm font-semibold text-foreground flex items-center gap-2">
                          <Building2 className="w-4 h-4 text-muted-foreground" />
                          Scraping Strategy <span className="text-destructive">*</span>
                        </label>
                        <div className="relative">
                          <select
                            value={newSource.scraping_strategy || 'direct_links'}
                            onChange={(e) => setNewSource({ ...newSource, scraping_strategy: e.target.value })}
                            className="w-full h-10 px-3 py-2 border border-border rounded-md bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 appearance-none cursor-pointer pr-8"
                          >
                            <option value="direct_links">Direct Links (PDF links directly in HTML)</option>
                            <option value="table_based">Table Based (PDFs in HTML tables)</option>
                            <option value="form_based">Form Based (PDFs via form submission)</option>
                          </select>
                          <div className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none">
                            <svg className="w-4 h-4 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                            </svg>
                          </div>
                        </div>
                        <p className="text-xs text-muted-foreground pl-6">
                          Select how PDFs are accessed on this website
                        </p>
                      </div>
                      {newSource.scraping_strategy === 'form_based' && (
                        <div className="space-y-4 pt-2 border-t border-border/50">
                          <div className="space-y-2">
                            <label className="text-sm font-semibold text-foreground flex items-center gap-2">
                              <FileText className="w-4 h-4 text-muted-foreground" />
                              Form Selector <span className="text-destructive">*</span>
                            </label>
                            <Input
                              type="text"
                              value={newSource.form_selector || ''}
                              onChange={(e) => setNewSource({ ...newSource, form_selector: e.target.value })}
                              placeholder="#download-file or .form-class"
                              className="h-10 font-mono text-sm"
                            />
                            <p className="text-xs text-muted-foreground pl-6">
                              CSS selector for the form element (e.g., #download-file, .form-class, or form[id="download-file"])
                            </p>
                          </div>
                          <div className="space-y-2">
                            <label className="text-sm font-semibold text-foreground flex items-center gap-2">
                              <FileText className="w-4 h-4 text-muted-foreground" />
                              Form Button Selector <span className="text-xs text-muted-foreground font-normal">(Optional)</span>
                            </label>
                            <Input
                              type="text"
                              value={newSource.form_button_selector || ''}
                              onChange={(e) => setNewSource({ ...newSource, form_button_selector: e.target.value })}
                              placeholder="#muat-turun or button[type='submit']"
                              className="h-10 font-mono text-sm"
                            />
                            <p className="text-xs text-muted-foreground pl-6">
                              CSS selector for the submit button (e.g., #muat-turun). If not provided, the form will be submitted directly.
                            </p>
                          </div>
                        </div>
                      )}
                    </div>
                    <div className="px-6 pb-6 border-t border-border bg-muted/30 pt-4">
                      <DialogFooter className="gap-2">
                        <Button
                          variant="outline"
                          onClick={handleCancelEdit}
                          className="flex-1 sm:flex-initial"
                        >
                          Cancel
                        </Button>
                        <Button 
                          onClick={handleAddSource} 
                          disabled={addingSource}
                          className="flex-1 sm:flex-initial"
                        >
                          {addingSource ? (
                            <>
                              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                              {editingSourceId ? 'Updating...' : 'Adding...'}
                            </>
                          ) : (
                            <>
                              {editingSourceId ? (
                                <>
                                  <Edit className="w-4 h-4 mr-2" />
                                  Update Source
                                </>
                              ) : (
                                <>
                                  <Plus className="w-4 h-4 mr-2" />
                                  Add Source
                                </>
                              )}
                            </>
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

              {/* Scheduled Scrapers Section */}
              <div className="mt-8">
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <h2 className="text-xl font-semibold text-foreground flex items-center gap-2">
                      <Calendar className="w-5 h-5" />
                      Scheduled Scrapers
                    </h2>
                    <p className="text-sm text-muted-foreground mt-1">
                      Automate knowledge updates with scheduled scraping jobs
                    </p>
                  </div>
                  <Dialog open={scheduleDialogOpen} onOpenChange={(open) => {
                    setScheduleDialogOpen(open);
                    if (open) {
                      // Reload sources when dialog opens to ensure we have the latest list
                      loadSources();
                    }
                  }}>
                    <DialogTrigger asChild>
                      <Button onClick={async () => {
                        setEditingScheduleId(null);
                        // Reload sources before opening dialog to ensure latest data
                        await loadSources();
                        setNewSchedule({
                          name: '',
                          source: 'all',
                          schedule_type: 'interval',
                          enabled: true,
                          interval_value: 6,
                          interval_unit: 'hours'
                        });
                      }}>
                        <Plus className="w-4 h-4 mr-2" />
                        Add Schedule
                      </Button>
                    </DialogTrigger>
                    <DialogContent className="p-0 max-w-2xl">
                      <div className="px-6 pt-6 pb-4">
                        <DialogHeader>
                          <div className="flex items-center gap-3 mb-2">
                            <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
                              <Calendar className="w-5 h-5 text-primary" />
                            </div>
                            <div className="flex-1">
                              <DialogTitle className="text-xl">{editingScheduleId ? 'Edit Schedule' : 'Add New Schedule'}</DialogTitle>
                              <DialogDescription className="mt-1.5">
                                {editingScheduleId 
                                  ? 'Update the scraper schedule configuration.'
                                  : 'Automate knowledge updates with scheduled scraping jobs. Set up recurring or one-time scraping tasks.'}
                              </DialogDescription>
                            </div>
                          </div>
                        </DialogHeader>
                      </div>
                      <div className="px-6 py-4 space-y-5 max-h-[60vh] overflow-y-auto scrollbar-hide">
                        <div className="space-y-2">
                          <label className="text-sm font-semibold text-foreground flex items-center gap-2">
                            <FileText className="w-4 h-4 text-muted-foreground" />
                            Schedule Name <span className="text-destructive">*</span>
                          </label>
                          <Input
                            type="text"
                            value={newSchedule.name}
                            onChange={(e) => setNewSchedule({ ...newSchedule, name: e.target.value })}
                            placeholder="e.g., Daily BNM Update"
                            className="h-10"
                          />
                        </div>
                        <div className="space-y-2">
                          <label className="text-sm font-semibold text-foreground flex items-center gap-2">
                            <Database className="w-4 h-4 text-muted-foreground" />
                            Source to Scrape <span className="text-destructive">*</span>
                          </label>
                          <div className="relative">
                            <select
                              value={newSchedule.source}
                              onChange={(e) => setNewSchedule({ ...newSchedule, source: e.target.value })}
                              className="w-full h-10 px-3 py-2 border border-border rounded-md bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 appearance-none cursor-pointer pr-8 disabled:opacity-50 disabled:cursor-not-allowed"
                              disabled={sources.length === 0 && newSchedule.source !== 'all'}
                            >
                              <option value="all">All Sources</option>
                              {sources.length > 0 ? (
                                sources.map((source) => (
                                  <option key={source.id} value={source.id}>{source.name}</option>
                                ))
                              ) : (
                                <option value="" disabled>No sources available</option>
                              )}
                            </select>
                            <div className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none">
                              <svg className="w-4 h-4 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                              </svg>
                            </div>
                          </div>
                          {sources.length === 0 && (
                            <p className="text-xs text-amber-600 dark:text-amber-400 pl-6 flex items-center gap-1">
                              <XCircle className="w-3 h-3" />
                              No sources available. Add a source first.
                            </p>
                          )}
                        </div>
                        <div className="space-y-2">
                          <label className="text-sm font-semibold text-foreground flex items-center gap-2">
                            <Clock className="w-4 h-4 text-muted-foreground" />
                            Schedule Type <span className="text-destructive">*</span>
                          </label>
                          <div className="relative">
                            <select
                              value={newSchedule.schedule_type || 'interval'}
                              onChange={(e) => {
                                const newType = e.target.value as 'interval' | 'cron' | 'once';
                                setNewSchedule({ 
                                  ...newSchedule, 
                                  schedule_type: newType,
                                  interval_value: newType === 'interval' ? 6 : undefined,
                                  interval_unit: newType === 'interval' ? 'hours' : undefined
                                });
                              }}
                              className="w-full h-10 px-3 py-2 border border-border rounded-md bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 appearance-none cursor-pointer pr-8"
                            >
                              <option value="interval">Interval (Every X time)</option>
                              <option value="cron">Cron (Advanced schedule)</option>
                              <option value="once">Once (One-time execution)</option>
                            </select>
                            <div className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none">
                              <svg className="w-4 h-4 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                              </svg>
                            </div>
                          </div>
                        </div>

                        {newSchedule.schedule_type === 'interval' && (
                          <div className="space-y-4 pt-2 border-t border-border/50">
                            <div className="grid grid-cols-2 gap-4">
                              <div className="space-y-2">
                                <label className="text-sm font-semibold text-foreground">Interval Value <span className="text-destructive">*</span></label>
                                <Input
                                  type="number"
                                  min="1"
                                  value={newSchedule.interval_value || ''}
                                  onChange={(e) => setNewSchedule({ ...newSchedule, interval_value: parseInt(e.target.value) || 1 })}
                                  placeholder="6"
                                  className="h-10"
                                />
                              </div>
                              <div className="space-y-2">
                                <label className="text-sm font-semibold text-foreground">Unit <span className="text-destructive">*</span></label>
                                <div className="relative">
                                  <select
                                    value={newSchedule.interval_unit || 'hours'}
                                    onChange={(e) => setNewSchedule({ ...newSchedule, interval_unit: e.target.value as any })}
                                    className="w-full h-10 px-3 py-2 border border-border rounded-md bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 appearance-none cursor-pointer pr-8"
                                  >
                                    <option value="minutes">Minutes</option>
                                    <option value="hours">Hours</option>
                                    <option value="days">Days</option>
                                  </select>
                                  <div className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none">
                                    <svg className="w-4 h-4 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                                    </svg>
                                  </div>
                                </div>
                              </div>
                            </div>
                            <div className="p-3 bg-primary/5 border border-primary/20 rounded-md">
                              <p className="text-xs text-foreground">
                                <span className="font-semibold">Preview:</span> This schedule will run every{' '}
                                <span className="font-semibold text-primary">
                                  {newSchedule.interval_value || 1} {newSchedule.interval_unit || 'hours'}
                                </span>
                              </p>
                            </div>
                          </div>
                        )}

                        {newSchedule.schedule_type === 'cron' && (
                          <div className="space-y-4 pt-2 border-t border-border/50">
                            <div className="p-3 bg-muted/50 border border-border rounded-md">
                              <p className="text-xs text-muted-foreground">
                                Use <code className="px-1.5 py-0.5 bg-background rounded text-foreground">*</code> for any value, or specify ranges (e.g., <code className="px-1.5 py-0.5 bg-background rounded text-foreground">0-23</code> for hours)
                              </p>
                            </div>
                            <div className="grid grid-cols-2 gap-4">
                              <div className="space-y-2">
                                <label className="text-sm font-semibold text-foreground">Hour (0-23)</label>
                                <Input
                                  type="text"
                                  value={newSchedule.cron_hour || '*'}
                                  onChange={(e) => setNewSchedule({ ...newSchedule, cron_hour: e.target.value })}
                                  placeholder="* or 0-23"
                                  className="h-10 font-mono text-sm"
                                />
                              </div>
                              <div className="space-y-2">
                                <label className="text-sm font-semibold text-foreground">Minute (0-59)</label>
                                <Input
                                  type="text"
                                  value={newSchedule.cron_minute || '*'}
                                  onChange={(e) => setNewSchedule({ ...newSchedule, cron_minute: e.target.value })}
                                  placeholder="* or 0-59"
                                  className="h-10 font-mono text-sm"
                                />
                              </div>
                              <div className="space-y-2">
                                <label className="text-sm font-semibold text-foreground">Day of Week (0-6)</label>
                                <Input
                                  type="text"
                                  value={newSchedule.cron_day_of_week || '*'}
                                  onChange={(e) => setNewSchedule({ ...newSchedule, cron_day_of_week: e.target.value })}
                                  placeholder="* or 0-6 (0=Monday)"
                                  className="h-10 font-mono text-sm"
                                />
                              </div>
                              <div className="space-y-2">
                                <label className="text-sm font-semibold text-foreground">Day of Month (1-31)</label>
                                <Input
                                  type="text"
                                  value={newSchedule.cron_day || '*'}
                                  onChange={(e) => setNewSchedule({ ...newSchedule, cron_day: e.target.value })}
                                  placeholder="* or 1-31"
                                  className="h-10 font-mono text-sm"
                                />
                              </div>
                            </div>
                            <div className="p-3 bg-primary/5 border border-primary/20 rounded-md">
                              <p className="text-xs text-foreground">
                                <span className="font-semibold">Example:</span>{' '}
                                <code className="px-1.5 py-0.5 bg-background rounded text-foreground">0 2 * * *</code> = Daily at 2:00 AM
                              </p>
                            </div>
                          </div>
                        )}

                        {newSchedule.schedule_type === 'once' && (
                          <div className="space-y-2 pt-2 border-t border-border/50">
                            <label className="text-sm font-semibold text-foreground flex items-center gap-2">
                              <Clock className="w-4 h-4 text-muted-foreground" />
                              Date & Time <span className="text-destructive">*</span>
                            </label>
                            <Input
                              type="datetime-local"
                              value={newSchedule.run_at ? newSchedule.run_at.slice(0, 16) : ''}
                              onChange={(e) => setNewSchedule({ ...newSchedule, run_at: e.target.value + ':00' })}
                              className="h-10"
                            />
                            {newSchedule.run_at && (
                              <div className="p-3 bg-primary/5 border border-primary/20 rounded-md">
                                <p className="text-xs text-foreground">
                                  <span className="font-semibold">Scheduled for:</span>{' '}
                                  <span className="font-semibold text-primary">
                                    {new Date(newSchedule.run_at).toLocaleString()}
                                  </span>
                                </p>
                              </div>
                            )}
                          </div>
                        )}

                        <div className="flex items-start gap-3 pt-2 border-t border-border/50">
                          <Checkbox
                            id="schedule-enabled"
                            checked={newSchedule.enabled !== false}
                            onCheckedChange={(checked) => setNewSchedule({ ...newSchedule, enabled: checked as boolean })}
                            className="mt-0.5"
                          />
                          <label htmlFor="schedule-enabled" className="text-sm text-foreground cursor-pointer flex-1">
                            <div className="font-semibold flex items-center gap-2">
                              Enable this schedule
                              {newSchedule.enabled !== false && (
                                <span className="text-xs px-2 py-0.5 bg-green-500/10 text-green-600 dark:text-green-400 rounded-full">
                                  Active
                                </span>
                              )}
                            </div>
                            <p className="text-xs text-muted-foreground mt-1">
                              {newSchedule.enabled !== false 
                                ? 'Schedule will run automatically according to the configuration'
                                : 'Schedule is disabled and will not run'}
                            </p>
                          </label>
                        </div>
                      </div>
                      <div className="px-6 pb-6 border-t border-border bg-muted/30 pt-4">
                        <DialogFooter className="gap-2">
                          <Button
                            variant="outline"
                            onClick={() => {
                              setScheduleDialogOpen(false);
                              setEditingScheduleId(null);
                            }}
                            className="flex-1 sm:flex-initial"
                          >
                            Cancel
                          </Button>
                          <Button 
                            onClick={async () => {
                              if (!newSchedule.name || !newSchedule.source) {
                                setError('Please fill in all required fields');
                                return;
                              }
                              try {
                                setAddingSchedule(true);
                                setError(null);
                                if (editingScheduleId) {
                                  await updateScraperSchedule(editingScheduleId, newSchedule);
                                } else {
                                  await createScraperSchedule(newSchedule);
                                }
                                await loadSchedules();
                                await loadSources();
                                setScheduleDialogOpen(false);
                                setEditingScheduleId(null);
                                setError(null);
                              } catch (err) {
                                setError(err instanceof Error ? err.message : 'Failed to save schedule');
                              } finally {
                                setAddingSchedule(false);
                              }
                            }}
                            disabled={addingSchedule}
                            className="flex-1 sm:flex-initial"
                          >
                            {addingSchedule ? (
                              <>
                                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                                {editingScheduleId ? 'Updating...' : 'Creating...'}
                              </>
                            ) : (
                              <>
                                {editingScheduleId ? (
                                  <>
                                    <Edit className="w-4 h-4 mr-2" />
                                    Update Schedule
                                  </>
                                ) : (
                                  <>
                                    <Plus className="w-4 h-4 mr-2" />
                                    Add Schedule
                                  </>
                                )}
                              </>
                            )}
                          </Button>
                        </DialogFooter>
                      </div>
                    </DialogContent>
                  </Dialog>
                </div>

                {schedules.length === 0 ? (
                  <div className="border border-border rounded-lg p-8 text-center">
                    <Calendar className="w-12 h-12 mx-auto mb-4 text-muted-foreground" />
                    <p className="text-muted-foreground">No scheduled scrapers yet</p>
                    <p className="text-sm text-muted-foreground mt-2">
                      Create a schedule to automate knowledge updates
                    </p>
                  </div>
                ) : (
                  <div className="space-y-2">
                    {schedules.map((schedule) => (
                      <div
                        key={schedule.id}
                        className="border border-border rounded-lg p-4 hover:border-primary/50 transition-colors"
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex-1">
                            <div className="flex items-center gap-3 mb-2">
                              <h3 className="font-semibold text-foreground">{schedule.name}</h3>
                              {schedule.enabled ? (
                                <span className="flex items-center gap-1 text-xs text-green-600 dark:text-green-400">
                                  <Power className="w-3 h-3" />
                                  Enabled
                                </span>
                              ) : (
                                <span className="flex items-center gap-1 text-xs text-muted-foreground">
                                  <PowerOff className="w-3 h-3" />
                                  Disabled
                                </span>
                              )}
                            </div>
                            <div className="text-sm text-muted-foreground space-y-1">
                              <p>Source: {getSourceName(schedule.source)}</p>
                              <p>Type: {schedule.schedule_type === 'interval' 
                                ? `Every ${schedule.interval_value} ${schedule.interval_unit}`
                                : schedule.schedule_type === 'cron'
                                ? `Cron: ${schedule.cron_hour || '*'} ${schedule.cron_minute || '*'} ${schedule.cron_day_of_week || '*'} ${schedule.cron_day || '*'}`
                                : `Once at ${schedule.run_at ? new Date(schedule.run_at).toLocaleString() : 'N/A'}`}
                              </p>
                              {schedule.next_run && (
                                <p className="text-primary">Next run: {new Date(schedule.next_run).toLocaleString()}</p>
                              )}
                              {schedule.last_run && (
                                <p>Last run: {new Date(schedule.last_run).toLocaleString()}</p>
                              )}
                            </div>
                          </div>
                          <div className="flex items-center gap-2">
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => {
                                setEditingScheduleId(schedule.id || null);
                                setNewSchedule({
                                  name: schedule.name,
                                  source: schedule.source,
                                  schedule_type: schedule.schedule_type,
                                  enabled: schedule.enabled,
                                  use_selenium: schedule.use_selenium,
                                  interval_value: schedule.interval_value,
                                  interval_unit: schedule.interval_unit,
                                  cron_hour: schedule.cron_hour,
                                  cron_minute: schedule.cron_minute,
                                  cron_day: schedule.cron_day,
                                  cron_day_of_week: schedule.cron_day_of_week,
                                  run_at: schedule.run_at
                                });
                                setScheduleDialogOpen(true);
                              }}
                            >
                              <Edit className="w-4 h-4" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={async () => {
                                if (!confirm('Are you sure you want to delete this schedule?')) return;
                                try {
                                  if (schedule.id) {
                                    await deleteScraperSchedule(schedule.id);
                                    await loadSchedules();
                                  }
                                } catch (err) {
                                  setError(err instanceof Error ? err.message : 'Failed to delete schedule');
                                }
                              }}
                            >
                              <Trash2 className="w-4 h-4 text-destructive" />
                            </Button>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        </ScrollArea>
      </div>
    </div>
  );
}
