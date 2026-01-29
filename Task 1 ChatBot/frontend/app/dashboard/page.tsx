'use client';

import { useState, useEffect } from 'react';
import { getAnalytics, AnalyticsResponse, CollectionStats, getCollections, getCollectionDocuments, CollectionDocumentsResponse, DocumentInfo, getRecentConversations } from '@/lib/api';
import { ScrollArea } from '@/components/ui/scroll-area';
import { FileText, Database, BarChart3, TrendingUp, Package, Loader2, Eye, ChevronDown, ChevronUp } from 'lucide-react';
import { Sidebar, ChatHistory } from '@/components/sidebar/sidebar';
import { SidebarToggle } from '@/components/sidebar/sidebar-toggle';
import { ThemeToggle } from '@/components/theme-toggle';
import { Sparkles } from 'lucide-react';
import { cn } from '@/lib/utils';

export default function DashboardPage() {
  const [analytics, setAnalytics] = useState<AnalyticsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [chatHistory, setChatHistory] = useState<ChatHistory[]>([]);
  const [availableCollections, setAvailableCollections] = useState<string[]>(['all', 'bnm_pdfs', 'iifa_resolutions', 'sc_resolutions']);
  const [selectedCollections, setSelectedCollections] = useState<string[]>(['all']);

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
      
      console.log('Dashboard: Loaded chat history:', history.length, 'sessions');
      setChatHistory(history);
      localStorage.setItem('chatHistory', JSON.stringify(history));
    } catch (err) {
      console.error('Failed to load chat history from backend:', err);
      // Fallback to local storage
      const savedHistory = localStorage.getItem('chatHistory');
      if (savedHistory) {
        try {
          const parsed = JSON.parse(savedHistory);
          console.log('Dashboard: Loaded chat history from localStorage:', parsed.length, 'sessions');
          setChatHistory(parsed);
        } catch (e) {
          console.error('Failed to load local chat history:', e);
        }
      }
    }
  };

  useEffect(() => {
    loadAnalytics();
    loadChatHistoryFromBackend();
    
    getCollections()
      .then((cols) => {
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
      })
      .catch((err) => {
        console.error('Failed to load collections:', err);
        // Fallback to default collections on error
        setAvailableCollections(['all', 'bnm_pdfs', 'iifa_resolutions', 'sc_resolutions']);
      });
  }, []);

  const loadAnalytics = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getAnalytics();
      setAnalytics(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load analytics');
      console.error('Error loading analytics:', err);
    } finally {
      setLoading(false);
    }
  };

  const getCollectionDisplayName = (name: string) => {
    const names: Record<string, string> = {
      'bnm_pdfs': 'Bank Negara Malaysia',
      'iifa_resolutions': 'IIFA Resolutions',
      'sc_resolutions': 'Securities Commission',
    };
    return names[name] || name.replace(/_/g, ' ').toUpperCase();
  };

  const getCollectionColor = (name: string) => {
    const colors: Record<string, string> = {
      'bnm_pdfs': 'bg-blue-500',
      'iifa_resolutions': 'bg-green-500',
      'sc_resolutions': 'bg-purple-500',
    };
    return colors[name] || 'bg-gray-500';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center space-y-4">
          <Loader2 className="w-8 h-8 animate-spin mx-auto text-primary" />
          <p className="text-muted-foreground">Loading analytics...</p>
        </div>
      </div>
    );
  }

  if (error) {
    const is503Error = error.includes('503') || error.includes('unavailable') || error.includes('not initialized');
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center space-y-4 max-w-lg px-4">
          <div className="text-destructive text-lg font-semibold">Error Loading Analytics</div>
          <p className="text-muted-foreground text-sm">{error}</p>
          {is503Error && (
            <div className="mt-4 p-4 bg-muted rounded-lg text-left space-y-2">
              <p className="text-sm font-semibold text-foreground">Troubleshooting Steps:</p>
              <ul className="text-xs text-muted-foreground space-y-1 list-disc list-inside">
                <li>Make sure the backend server is running on port 8000</li>
                <li>Check if Qdrant vector database is running and accessible</li>
                <li>Verify the RAG service initialized successfully (check backend logs)</li>
                <li>Ensure all required environment variables are set in the backend</li>
              </ul>
            </div>
          )}
          <button
            onClick={loadAnalytics}
            className="px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!analytics) {
    return null;
  }

  return (
    <div className="flex h-screen bg-background">
      {/* Sidebar */}
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

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <header className="border-b border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
          <div className="px-4 py-4">
            <div className="flex items-center justify-between gap-3">
              <div className="flex items-center gap-3">
                <SidebarToggle onToggle={() => setSidebarOpen(!sidebarOpen)} />
                <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center">
                  <Sparkles className="w-5 h-5 text-primary-foreground" />
                </div>
                <div className="min-w-0 flex-1">
                  <h1 className="text-lg sm:text-xl font-semibold text-foreground truncate">Analytics Dashboard</h1>
                  <p className="text-xs text-muted-foreground hidden sm:block">RAG Data Source Monitoring</p>
                </div>
              </div>
              <ThemeToggle />
            </div>
          </div>
        </header>

        {/* Dashboard Content */}
        <ScrollArea className="flex-1">
          <div className="container mx-auto px-4 sm:px-6 py-4 sm:py-8">

        {/* Summary Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4 mb-6 sm:mb-8">
          <StatCard
            title="Total Collections"
            value={analytics.total_collections}
            icon={<Database className="w-5 h-5" />}
            color="bg-blue-500"
          />
          <StatCard
            title="Total Documents"
            value={analytics.total_documents.toLocaleString()}
            icon={<FileText className="w-5 h-5" />}
            color="bg-green-500"
          />
          <StatCard
            title="Total Chunks"
            value={analytics.total_chunks.toLocaleString()}
            icon={<Package className="w-5 h-5" />}
            color="bg-purple-500"
          />
          <StatCard
            title="Qdrant Status"
            value={analytics.qdrant_status}
            icon={<BarChart3 className="w-5 h-5" />}
            color={analytics.qdrant_status === 'connected' ? 'bg-green-500' : 'bg-red-500'}
          />
        </div>

        {/* System Info */}
        <div className="bg-card border border-border rounded-lg p-4 sm:p-6 mb-6 sm:mb-8">
          <h2 className="text-lg sm:text-xl font-semibold text-foreground mb-3 sm:mb-4 flex items-center gap-2">
            <Database className="w-4 h-4 sm:w-5 sm:h-5" />
            System Information
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4">
            <div>
              <p className="text-sm text-muted-foreground mb-1">Embedding Model</p>
              <p className="text-foreground font-medium">{analytics.embedding_model}</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground mb-1">Vector Database</p>
              <p className="text-foreground font-medium">
                Qdrant - <span className={cn(
                  analytics.qdrant_status === 'connected' ? 'text-green-500' : 'text-red-500'
                )}>
                  {analytics.qdrant_status}
                </span>
              </p>
            </div>
          </div>
        </div>

        {/* Collection Details */}
        <div className="bg-card border border-border rounded-lg p-4 sm:p-6">
          <h2 className="text-lg sm:text-xl font-semibold text-foreground mb-3 sm:mb-4 flex items-center gap-2">
            <TrendingUp className="w-4 h-4 sm:w-5 sm:h-5" />
            Collection Statistics
          </h2>
          <ScrollArea className="h-[500px]">
            <div className="space-y-4 pr-4">
              {analytics.collections.map((collection) => (
                <CollectionCard
                  key={collection.collection_name}
                  collection={collection}
                  displayName={getCollectionDisplayName(collection.collection_name)}
                  color={getCollectionColor(collection.collection_name)}
                />
              ))}
              {analytics.collections.length === 0 && (
                <div className="text-center py-8 text-muted-foreground">
                  No collections found
                </div>
              )}
            </div>
          </ScrollArea>
        </div>
          </div>
        </ScrollArea>
      </div>
    </div>
  );
}

interface StatCardProps {
  title: string;
  value: string | number;
  icon: React.ReactNode;
  color: string;
}

function StatCard({ title, value, icon, color }: StatCardProps) {
  return (
    <div className="bg-card border border-border rounded-lg p-6">
      <div className="flex items-center justify-between mb-2">
        <p className="text-sm text-muted-foreground">{title}</p>
        <div className={cn('p-2 rounded-lg text-white', color)}>
          {icon}
        </div>
      </div>
      <p className="text-2xl font-bold text-foreground">{value}</p>
    </div>
  );
}

interface CollectionCardProps {
  collection: CollectionStats;
  displayName: string;
  color: string;
}

function CollectionCard({ collection, displayName, color }: CollectionCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [documents, setDocuments] = useState<DocumentInfo[]>([]);
  const [loadingDocuments, setLoadingDocuments] = useState(false);
  const [documentsError, setDocumentsError] = useState<string | null>(null);

  const formatDate = (dateStr?: string) => {
    if (!dateStr) return 'N/A';
    try {
      // Try to parse various date formats
      const date = new Date(dateStr);
      if (isNaN(date.getTime())) {
        // If not a standard date format, return as-is
        return dateStr;
      }
      return date.toLocaleDateString('en-US', { 
        year: 'numeric', 
        month: 'short', 
        day: 'numeric' 
      });
    } catch {
      return dateStr;
    }
  };

  const handleToggleDocuments = async () => {
    if (!isExpanded && documents.length === 0) {
      // Load documents when expanding for the first time
      setLoadingDocuments(true);
      setDocumentsError(null);
      try {
        const data = await getCollectionDocuments(collection.collection_name);
        setDocuments(data.documents);
      } catch (err) {
        setDocumentsError(err instanceof Error ? err.message : 'Failed to load documents');
        console.error('Error loading documents:', err);
      } finally {
        setLoadingDocuments(false);
      }
    }
    setIsExpanded(!isExpanded);
  };

  return (
    <div className="bg-background border border-border rounded-lg p-4 sm:p-6 hover:border-primary/50 transition-colors">
      <div className="flex items-start justify-between mb-3 sm:mb-4">
        <div className="flex items-center gap-2 sm:gap-3 min-w-0 flex-1">
          <div className={cn('w-3 h-3 rounded-full flex-shrink-0', color)} />
          <div className="min-w-0 flex-1">
            <h3 className="text-base sm:text-lg font-semibold text-foreground truncate">{displayName}</h3>
            <p className="text-xs text-muted-foreground truncate">{collection.collection_name}</p>
          </div>
        </div>
      </div>
      
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 sm:gap-4 mb-3 sm:mb-4">
        <div>
          <p className="text-xs text-muted-foreground mb-1">Documents</p>
          <p className="text-lg font-semibold text-foreground">
            {collection.total_documents.toLocaleString()}
          </p>
        </div>
        <div>
          <p className="text-xs text-muted-foreground mb-1">Chunks</p>
          <p className="text-lg font-semibold text-foreground">
            {collection.total_chunks.toLocaleString()}
          </p>
        </div>
        <div>
          <p className="text-xs text-muted-foreground mb-1">Unique PDFs</p>
          <p className="text-lg font-semibold text-foreground">
            {collection.unique_pdfs.toLocaleString()}
          </p>
        </div>
        <div>
          <p className="text-xs text-muted-foreground mb-1">Avg Chunks/Doc</p>
          <p className="text-lg font-semibold text-foreground">
            {collection.avg_chunks_per_document.toFixed(1)}
          </p>
        </div>
      </div>

      {/* Update Times */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4 pt-3 sm:pt-4 border-t border-border mb-3 sm:mb-4">
        <div>
          <p className="text-xs text-muted-foreground mb-1">Collection Last Updated</p>
          <p className="text-sm font-medium text-foreground">
            {formatDate(collection.last_updated)}
          </p>
          {collection.last_updated && (
            <p className="text-xs text-muted-foreground mt-1">
              Raw: {collection.last_updated}
            </p>
          )}
        </div>
        <div>
          <p className="text-xs text-muted-foreground mb-1">Last Document Updated</p>
          <p className="text-sm font-medium text-foreground">
            {formatDate(collection.last_document_updated)}
          </p>
          {collection.last_document_updated && (
            <p className="text-xs text-muted-foreground mt-1">
              Raw: {collection.last_document_updated}
            </p>
          )}
          {collection.last_document_title && (
            <p className="text-xs text-muted-foreground mt-1 line-clamp-1">
              From: {collection.last_document_title}
            </p>
          )}
        </div>
      </div>

      {/* Documents List Toggle */}
      <div className="border-t border-border pt-4">
        <button
          onClick={handleToggleDocuments}
          className="w-full flex items-center justify-between text-sm font-medium text-foreground hover:text-primary transition-colors"
        >
          <span className="flex items-center gap-2">
            <FileText className="w-4 h-4" />
            View Documents ({collection.total_documents})
          </span>
          {isExpanded ? (
            <ChevronUp className="w-4 h-4" />
          ) : (
            <ChevronDown className="w-4 h-4" />
          )}
        </button>

        {/* Documents List */}
        {isExpanded && (
          <div className="mt-3 sm:mt-4 space-y-2 max-h-[300px] sm:max-h-[400px] overflow-y-auto">
            {loadingDocuments ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="w-5 h-5 animate-spin text-primary" />
                <span className="ml-2 text-sm text-muted-foreground">Loading documents...</span>
              </div>
            ) : documentsError ? (
              <div className="text-sm text-destructive py-4 text-center">
                {documentsError}
              </div>
            ) : documents.length === 0 ? (
              <div className="text-sm text-muted-foreground py-4 text-center">
                No documents found
              </div>
            ) : (
              documents.map((doc, index) => (
                <div
                  key={index}
                  className="flex items-center justify-between p-2 sm:p-3 rounded-lg border border-border bg-card hover:bg-accent/50 transition-colors"
                >
                  <div className="flex-1 min-w-0 pr-2">
                    <p className="text-xs sm:text-sm font-medium text-foreground truncate">
                      {doc.pdf_title}
                    </p>
                    <div className="flex flex-wrap items-center gap-2 sm:gap-3 mt-1 text-xs text-muted-foreground">
                      {doc.date && <span className="whitespace-nowrap">{formatDate(doc.date)}</span>}
                      {doc.document_type && <span className="hidden sm:inline">• {doc.document_type}</span>}
                      {doc.resolution_number && <span className="hidden sm:inline">• Resolution #{doc.resolution_number}</span>}
                      {doc.total_chunks > 0 && <span className="hidden sm:inline">• {doc.total_chunks} chunks</span>}
                    </div>
                  </div>
                  {doc.pdf_url && (
                    <a
                      href={doc.pdf_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="ml-2 sm:ml-3 p-1.5 sm:p-2 rounded-lg hover:bg-accent transition-colors flex-shrink-0 touch-target"
                      title="View source document"
                      aria-label={`View ${doc.pdf_title}`}
                    >
                      <Eye className="w-4 h-4 text-primary" />
                    </a>
                  )}
                </div>
              ))
            )}
          </div>
        )}
      </div>
    </div>
  );
}
