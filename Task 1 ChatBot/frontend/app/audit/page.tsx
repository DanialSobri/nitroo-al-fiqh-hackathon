'use client';

import React, { useState, useEffect } from 'react';
import { getAuditLogs, getAuditStatistics, AuditLogEntry, AuditLogStatistics, getCollections, getRecentConversations } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Input } from '@/components/ui/input';
import { RefreshCw, Download, Filter, TrendingUp, Eye, ChevronDown, ChevronUp } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog';
import { Sidebar, ChatHistory } from '@/components/sidebar/sidebar';
import { SidebarToggle } from '@/components/sidebar/sidebar-toggle';

export default function AuditLogsPage() {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [collections, setCollections] = useState<string[]>(['all', 'bnm_pdfs', 'iifa_resolutions', 'sc_resolutions']);
  const [selectedCollections, setSelectedCollections] = useState<string[]>(['all']);
  const [chatHistory, setChatHistory] = useState<ChatHistory[]>([]);
  const [logs, setLogs] = useState<AuditLogEntry[]>([]);
  const [statistics, setStatistics] = useState<AuditLogStatistics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [limit, setLimit] = useState(100);
  const [offset, setOffset] = useState(0);
  const [total, setTotal] = useState(0);
  const [filters, setFilters] = useState({
    llm_provider: 'all',
    success_only: false,
    start_date: '',
    end_date: '',
  });
  const [expandedRows, setExpandedRows] = useState<Set<number>>(new Set());
  const [selectedAnswer, setSelectedAnswer] = useState<{ question: string; answer: string } | null>(null);

  const loadLogs = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await getAuditLogs(
        limit,
        offset,
        filters.llm_provider === 'all' ? undefined : filters.llm_provider,
        filters.success_only,
        filters.start_date || undefined,
        filters.end_date || undefined
      );
      setLogs(response.logs);
      setTotal(response.total);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load audit logs');
    } finally {
      setLoading(false);
    }
  };

  const loadStatistics = async () => {
    try {
      const stats = await getAuditStatistics();
      setStatistics(stats);
    } catch (err) {
      console.error('Failed to load statistics:', err);
    }
  };

  // Ensure llm_provider is never empty
  useEffect(() => {
    if (!filters.llm_provider || filters.llm_provider === '') {
      setFilters(prev => ({ ...prev, llm_provider: 'all' }));
    }
  }, [filters.llm_provider]);

  useEffect(() => {
    loadLogs();
    loadStatistics();
  }, [limit, offset, filters]);

  const formatDate = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleString();
  };

  const formatDuration = (ms: number | null | undefined) => {
    if (!ms) return 'N/A';
    if (ms < 1000) return `${ms}ms`;
    return `${(ms / 1000).toFixed(2)}s`;
  };

  const exportLogs = () => {
    const csv = [
      ['Timestamp', 'Question', 'Answer', 'LLM Provider', 'Model', 'Prompt Tokens', 'Completion Tokens', 'Total Tokens', 'Collections', 'Sources Found', 'Sources Cited', 'Response Time (ms)', 'Success'].join(','),
      ...logs.map(log => [
        log.timestamp,
        `"${log.question.replace(/"/g, '""')}"`,
        `"${(log.answer || log.error_message || '').replace(/"/g, '""')}"`,
        log.llm_provider,
        log.llm_model,
        log.prompt_tokens || '',
        log.completion_tokens || '',
        log.total_tokens || '',
        log.collections_searched.join(';'),
        log.num_sources_found,
        log.num_sources_cited,
        log.response_time_ms || '',
        log.success ? 'Yes' : 'No',
      ].join(','))
    ].join('\n');

    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `audit_logs_${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    window.URL.revokeObjectURL(url);
  };

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

  // Load collections for sidebar
  useEffect(() => {
    const loadCollections = async () => {
      try {
        const cols = await getCollections();
        // Ensure we always have the default collections even if API returns empty or only 'all'
        const defaultCollections = ['all', 'bnm_pdfs', 'iifa_resolutions', 'sc_resolutions'];
        if (cols && cols.length > 0) {
          // Merge API collections with defaults, removing duplicates
          const merged = ['all', ...new Set([...cols.filter(c => c !== 'all'), ...defaultCollections.filter(c => c !== 'all')])];
          setCollections(merged);
        } else {
          // Fallback to defaults if API returns empty
          setCollections(defaultCollections);
        }
      } catch (err) {
        console.error('Failed to load collections:', err);
        // Fallback to default collections on error
        setCollections(['all', 'bnm_pdfs', 'iifa_resolutions', 'sc_resolutions']);
      }
    };
    loadCollections();
    loadChatHistoryFromBackend();
  }, []);

  return (
    <div className="flex h-screen bg-background w-full">
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
        collections={collections}
        selectedCollections={selectedCollections}
        onCollectionsChange={setSelectedCollections}
      />

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden w-full min-w-0">
        {/* Header */}
        <header className="border-b border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 w-full">
          <div className="px-4 py-4 w-full">
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 w-full">
              <div className="flex items-center gap-3">
                <SidebarToggle onToggle={() => setSidebarOpen(!sidebarOpen)} />
                <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center">
                  <TrendingUp className="w-5 h-5 text-primary-foreground" />
                </div>
                <div className="min-w-0 flex-1">
                  <h1 className="text-lg sm:text-xl font-semibold text-foreground truncate">Audit Logs</h1>
                  <p className="text-xs text-muted-foreground hidden sm:block">Track token usage and query history</p>
                </div>
              </div>
              <div className="flex gap-2 w-full sm:w-auto">
                <Button onClick={loadLogs} variant="outline" size="sm" className="flex-1 sm:flex-initial">
                  <RefreshCw className="w-4 h-4 mr-2" />
                  Refresh
                </Button>
                <Button onClick={exportLogs} variant="outline" size="sm" className="flex-1 sm:flex-initial">
                  <Download className="w-4 h-4 mr-2" />
                  Export CSV
                </Button>
              </div>
            </div>
          </div>
        </header>

        {/* Content */}
        <div className="flex-1 overflow-y-auto w-full">
          <div className="w-full p-4 sm:p-6 space-y-4 sm:space-y-6">
            {/* Statistics Cards */}
            {statistics && (
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="bg-card border rounded-lg p-4">
                  <div className="text-sm text-muted-foreground">Total Queries</div>
                  <div className="text-2xl font-bold mt-1">{statistics.total_queries}</div>
                  <div className="text-xs text-muted-foreground mt-1">
                    {statistics.successful_queries} successful, {statistics.failed_queries} failed
                  </div>
                </div>
                <div className="bg-card border rounded-lg p-4">
                  <div className="text-sm text-muted-foreground">Total Tokens</div>
                  <div className="text-2xl font-bold mt-1">
                    {statistics.total_tokens.toLocaleString()}
                  </div>
                  <div className="text-xs text-muted-foreground mt-1">
                    Avg: {statistics.average_tokens_per_query.toFixed(0)} per query
                  </div>
                </div>
                <div className="bg-card border rounded-lg p-4">
                  <div className="text-sm text-muted-foreground">Success Rate</div>
                  <div className="text-2xl font-bold mt-1">
                    {statistics.total_queries > 0
                      ? ((statistics.successful_queries / statistics.total_queries) * 100).toFixed(1)
                      : 0}%
                  </div>
                </div>
                <div className="bg-card border rounded-lg p-4">
                  <div className="text-sm text-muted-foreground">Providers</div>
                  <div className="text-2xl font-bold mt-1">
                    {statistics.token_usage_by_provider.length}
                  </div>
                  <div className="text-xs text-muted-foreground mt-1">
                    {statistics.token_usage_by_provider.map(p => p.llm_provider).join(', ')}
                  </div>
                </div>
              </div>
            )}

            {/* Filters */}
            <div className="bg-card border rounded-lg p-4 space-y-4">
              <div className="flex items-center gap-2">
                <Filter className="w-4 h-4" />
                <h3 className="font-semibold">Filters</h3>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                <div>
                  <label className="text-sm text-muted-foreground mb-1 block">LLM Provider</label>
                  <Select
                    value={filters.llm_provider || "all"}
                    onValueChange={(value) => {
                      if (value && value !== "") {
                        setFilters({ ...filters, llm_provider: value });
                      }
                    }}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="All providers" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All providers</SelectItem>
                      <SelectItem value="ollama">Ollama</SelectItem>
                      <SelectItem value="openai">OpenAI</SelectItem>
                      <SelectItem value="api_gateway">API Gateway</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <label className="text-sm text-muted-foreground mb-1 block">Start Date</label>
                  <Input
                    type="date"
                    value={filters.start_date}
                    onChange={(e) => setFilters({ ...filters, start_date: e.target.value })}
                  />
                </div>
                <div>
                  <label className="text-sm text-muted-foreground mb-1 block">End Date</label>
                  <Input
                    type="date"
                    value={filters.end_date}
                    onChange={(e) => setFilters({ ...filters, end_date: e.target.value })}
                  />
                </div>
                <div className="flex items-end">
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={filters.success_only}
                      onChange={(e) => setFilters({ ...filters, success_only: e.target.checked })}
                      className="w-4 h-4"
                    />
                    <span className="text-sm">Success only</span>
                  </label>
                </div>
              </div>
            </div>

            {/* Logs Table */}
            <div className="bg-card border rounded-lg w-full overflow-visible">
              {loading ? (
                <div className="p-8 text-center text-muted-foreground">Loading audit logs...</div>
              ) : error ? (
                <div className="p-8 text-center text-destructive">{error}</div>
              ) : logs.length === 0 ? (
                <div className="p-8 text-center text-muted-foreground">No audit logs found</div>
              ) : (
                <>
                  {/* Mobile Card View */}
                  <div className="block md:hidden space-y-4 p-4">
                    {logs.map((log) => {
                      const isExpanded = expandedRows.has(log.id);
                      const answerPreview = log.answer 
                        ? (log.answer.length > 100 ? log.answer.substring(0, 100) + '...' : log.answer)
                        : log.error_message || 'No answer available';
                      
                      return (
                        <div key={log.id} className="border rounded-lg p-4 space-y-3">
                          <div className="flex items-start justify-between gap-2">
                            <div className="flex-1 min-w-0">
                              <div className="text-xs text-muted-foreground mb-1">
                                {formatDate(log.timestamp)}
                              </div>
                              <div className="font-semibold text-sm mb-2">{log.question}</div>
                              <div className="text-sm text-muted-foreground mb-2">
                                {answerPreview}
                              </div>
                            </div>
                            <div className="flex flex-col items-end gap-2">
                              <span
                                className={`px-2 py-1 rounded text-xs whitespace-nowrap ${
                                  log.success
                                    ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                                    : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
                                }`}
                              >
                                {log.success ? 'Success' : 'Failed'}
                              </span>
                              {log.answer && (
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  className="h-8 px-2 text-xs"
                                  onClick={() => setSelectedAnswer({ question: log.question, answer: log.answer || '' })}
                                >
                                  <Eye className="h-3 w-3 mr-1" />
                                  View
                                </Button>
                              )}
                            </div>
                          </div>
                          <div className="grid grid-cols-2 gap-2 text-xs">
                            <div>
                              <span className="text-muted-foreground">Provider:</span> {log.llm_provider}
                            </div>
                            <div>
                              <span className="text-muted-foreground">Model:</span> {log.llm_model}
                            </div>
                            <div>
                              <span className="text-muted-foreground">Tokens:</span> {log.total_tokens?.toLocaleString() || '-'}
                            </div>
                            <div>
                              <span className="text-muted-foreground">Time:</span> {formatDuration(log.response_time_ms)}
                            </div>
                            <div className="col-span-2">
                              <span className="text-muted-foreground">Sources:</span> {log.num_sources_found} / {log.num_sources_cited}
                            </div>
                          </div>
                          {isExpanded && log.answer && (
                            <div className="pt-3 border-t space-y-2">
                              <div className="text-sm font-semibold">Full Answer:</div>
                              <div className="text-sm whitespace-pre-wrap">{log.answer}</div>
                            </div>
                          )}
                          {log.answer && (
                            <Button
                              variant="ghost"
                              size="sm"
                              className="w-full text-xs"
                              onClick={() => {
                                const newExpanded = new Set(expandedRows);
                                if (isExpanded) {
                                  newExpanded.delete(log.id);
                                } else {
                                  newExpanded.add(log.id);
                                }
                                setExpandedRows(newExpanded);
                              }}
                            >
                              {isExpanded ? (
                                <>Hide Answer <ChevronUp className="h-3 w-3 ml-1" /></>
                              ) : (
                                <>Show Full Answer <ChevronDown className="h-3 w-3 ml-1" /></>
                              )}
                            </Button>
                          )}
                        </div>
                      );
                    })}
                  </div>

                  {/* Desktop Table View */}
                  <div className="hidden md:block w-full">
                    <div className="overflow-x-auto overflow-y-auto" style={{ maxHeight: '600px' }}>
                      <Table className="w-full" style={{ minWidth: '1200px' }}>
                      <TableHeader>
                        <TableRow>
                          <TableHead className="w-12"></TableHead>
                          <TableHead className="min-w-[150px]">Timestamp</TableHead>
                          <TableHead className="min-w-[200px]">Question</TableHead>
                          <TableHead className="min-w-[250px]">Answer Preview</TableHead>
                          <TableHead className="hidden lg:table-cell">Provider</TableHead>
                          <TableHead className="hidden xl:table-cell">Model</TableHead>
                          <TableHead className="text-right hidden xl:table-cell">Prompt Tokens</TableHead>
                          <TableHead className="text-right hidden xl:table-cell">Completion Tokens</TableHead>
                          <TableHead className="text-right min-w-[100px]">Total Tokens</TableHead>
                          <TableHead className="hidden lg:table-cell">Collections</TableHead>
                          <TableHead className="text-right min-w-[80px]">Sources</TableHead>
                          <TableHead className="text-right hidden xl:table-cell">Response Time</TableHead>
                          <TableHead className="min-w-[80px]">Status</TableHead>
                        </TableRow>
                      </TableHeader>
                    <TableBody>
                      {logs.map((log) => {
                        const isExpanded = expandedRows.has(log.id);
                        const answerPreview = log.answer 
                          ? (log.answer.length > 100 ? log.answer.substring(0, 100) + '...' : log.answer)
                          : log.error_message || 'No answer available';
                        
                        return (
                          <React.Fragment key={log.id}>
                            <TableRow>
                              <TableCell>
                                {log.answer && (
                                  <Button
                                    variant="ghost"
                                    size="icon"
                                    className="h-6 w-6"
                                    onClick={() => {
                                      const newExpanded = new Set(expandedRows);
                                      if (isExpanded) {
                                        newExpanded.delete(log.id);
                                      } else {
                                        newExpanded.add(log.id);
                                      }
                                      setExpandedRows(newExpanded);
                                    }}
                                  >
                                    {isExpanded ? (
                                      <ChevronUp className="h-4 w-4" />
                                    ) : (
                                      <ChevronDown className="h-4 w-4" />
                                    )}
                                  </Button>
                                )}
                              </TableCell>
                              <TableCell className="text-xs">
                                {formatDate(log.timestamp)}
                              </TableCell>
                              <TableCell className="max-w-xs truncate" title={log.question}>
                                {log.question}
                              </TableCell>
                              <TableCell className="max-w-md">
                                <div className="flex items-center gap-2">
                                  <span className="truncate text-sm" title={log.answer || log.error_message || ''}>
                                    {answerPreview}
                                  </span>
                                  {log.answer && log.answer.length > 100 && (
                                    <Button
                                      variant="ghost"
                                      size="sm"
                                      className="h-6 px-2 text-xs flex-shrink-0"
                                      onClick={() => setSelectedAnswer({ question: log.question, answer: log.answer || '' })}
                                    >
                                      <Eye className="h-3 w-3 mr-1" />
                                      View
                                    </Button>
                                  )}
                                </div>
                              </TableCell>
                              <TableCell className="hidden lg:table-cell">{log.llm_provider}</TableCell>
                              <TableCell className="text-xs hidden xl:table-cell">{log.llm_model}</TableCell>
                              <TableCell className="text-right hidden xl:table-cell">
                                {log.prompt_tokens?.toLocaleString() || '-'}
                              </TableCell>
                              <TableCell className="text-right hidden xl:table-cell">
                                {log.completion_tokens?.toLocaleString() || '-'}
                              </TableCell>
                              <TableCell className="text-right font-semibold">
                                {log.total_tokens?.toLocaleString() || '-'}
                              </TableCell>
                              <TableCell className="text-xs hidden lg:table-cell">
                                {log.collections_searched.join(', ') || '-'}
                              </TableCell>
                              <TableCell className="text-right">
                                {log.num_sources_found} / {log.num_sources_cited}
                              </TableCell>
                              <TableCell className="text-right text-xs hidden xl:table-cell">
                                {formatDuration(log.response_time_ms)}
                              </TableCell>
                              <TableCell>
                                <span
                                  className={`px-2 py-1 rounded text-xs ${
                                    log.success
                                      ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                                      : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
                                  }`}
                                >
                                  {log.success ? 'Success' : 'Failed'}
                                </span>
                              </TableCell>
                            </TableRow>
                            {isExpanded && log.answer && (
                              <TableRow>
                                <TableCell colSpan={13} className="bg-muted/30">
                                  <div className="p-4 space-y-2">
                                    <div className="text-sm font-semibold">Question:</div>
                                    <div className="text-sm text-muted-foreground">{log.question}</div>
                                    <div className="text-sm font-semibold mt-4">Answer:</div>
                                    <div className="text-sm whitespace-pre-wrap">{log.answer}</div>
                                    {log.error_message && (
                                      <>
                                        <div className="text-sm font-semibold mt-4 text-destructive">Error:</div>
                                        <div className="text-sm text-destructive">{log.error_message}</div>
                                      </>
                                    )}
                                  </div>
                                </TableCell>
                              </TableRow>
                            )}
                          </React.Fragment>
                        );
                      })}
                    </TableBody>
                  </Table>
                    </div>
                </div>
                </>
              )}

              {/* Pagination */}
              {total > 0 && (
                <div className="p-4 border-t flex flex-col sm:flex-row items-center justify-between gap-4">
                  <div className="text-sm text-muted-foreground text-center sm:text-left">
                    Showing {offset + 1} to {Math.min(offset + limit, total)} of {total} logs
                  </div>
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setOffset(Math.max(0, offset - limit))}
                      disabled={offset === 0}
                    >
                      Previous
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setOffset(offset + limit)}
                      disabled={offset + limit >= total}
                    >
                      Next
                    </Button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Answer Dialog */}
      <Dialog open={!!selectedAnswer} onOpenChange={(open) => !open && setSelectedAnswer(null)}>
        <DialogContent className="w-[95vw] sm:w-full max-w-3xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Full Answer</DialogTitle>
            <DialogDescription>
              {selectedAnswer?.question}
            </DialogDescription>
          </DialogHeader>
          <div className="mt-4">
            <div className="text-sm font-semibold mb-2">Answer:</div>
            <div className="text-sm whitespace-pre-wrap bg-muted p-4 rounded-lg">
              {selectedAnswer?.answer}
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
