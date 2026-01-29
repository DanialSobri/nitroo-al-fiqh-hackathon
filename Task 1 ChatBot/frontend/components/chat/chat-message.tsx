'use client';

import { useState, useRef } from 'react';
import { SourceReference, findReferencePage } from '@/lib/api';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Button } from '@/components/ui/button';
import { FileText, ExternalLink, ThumbsUp, ThumbsDown, Copy, Check, Link as LinkIcon, Loader2, Clock } from 'lucide-react';
import { cn } from '@/lib/utils';

interface ChatMessageProps {
  question: string;
  answer: string;
  references: SourceReference[];
  isLoading?: boolean;
  messageId?: string;
  onFeedback?: (messageId: string, feedback: 'good' | 'bad' | null) => void;
  initialFeedback?: 'good' | 'bad' | null;
  citationMap?: { [key: number]: number } | null;
  responseTimeMs?: number;
}

interface AnswerWithCitationsProps {
  answer: string;
  references: SourceReference[];
  citationMap?: { [key: number]: number } | null;
  messageId?: string;
  onCitationClick: (refIndex: number) => void;
}

// Helper function to format duration
function formatDuration(ms: number | null | undefined): string {
  if (!ms) return 'N/A';
  if (ms < 1000) return `${ms}ms`;
  return `${(ms / 1000).toFixed(2)}s`;
}

// Helper function to format retrieval time
function formatRetrievalTime(isoString: string): string {
  try {
    const date = new Date(isoString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffSecs = Math.floor(diffMs / 1000);
    const diffMins = Math.floor(diffSecs / 60);
    
    if (diffSecs < 60) {
      return 'just now';
    } else if (diffMins < 60) {
      return `${diffMins}m ago`;
    } else {
      const diffHours = Math.floor(diffMins / 60);
      if (diffHours < 24) {
        return `${diffHours}h ago`;
      } else {
        return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
      }
    }
  } catch {
    return new Date(isoString).toLocaleString();
  }
}

function AnswerWithCitations({ answer, references, citationMap, messageId, onCitationClick }: AnswerWithCitationsProps) {
  // Parse citations like [1], [2], etc. and make them clickable
  const parseCitations = (text: string) => {
    // Match citation patterns like [1], [2], [12], etc.
    const citationRegex = /\[(\d+)\]/g;
    const parts: (string | { type: 'citation'; num: number; refIndex: number })[] = [];
    let lastIndex = 0;
    let match;

    while ((match = citationRegex.exec(text)) !== null) {
      // Add text before citation
      if (match.index > lastIndex) {
        parts.push(text.substring(lastIndex, match.index));
      }
      
      // Add citation
      const citationNum = parseInt(match[1], 10);
      // Map citation number to reference index (citation numbers are 1-indexed, references are 0-indexed)
      // If citationMap is provided, use it; otherwise assume citation number directly maps to index
      const refIndex = citationMap ? (citationMap[citationNum] ?? citationNum - 1) : citationNum - 1;
      
      if (refIndex >= 0 && refIndex < references.length) {
        parts.push({ type: 'citation', num: citationNum, refIndex });
      } else {
        // Invalid citation - still style it but mark as invalid
        parts.push({ type: 'citation', num: citationNum, refIndex: -1 });
      }
      
      lastIndex = match.index + match[0].length;
    }
    
    // Add remaining text
    if (lastIndex < text.length) {
      parts.push(text.substring(lastIndex));
    }
    
    return parts.length > 0 ? parts : [text];
  };

  const parts = parseCitations(answer);

  return (
    <p className="text-foreground/90 leading-relaxed whitespace-pre-wrap">
      {parts.map((part, index) => {
        if (typeof part === 'string') {
          return <span key={index}>{part}</span>;
        } else {
          // Check if citation is valid
          const isValidCitation = part.refIndex >= 0 && part.refIndex < references.length;
          const ref = isValidCitation ? references[part.refIndex] : null;
          
          if (!isValidCitation || !ref) {
            // Invalid citation - still style it but show as unavailable
            return (
              <span
                key={index}
                className="inline-flex items-center gap-1 min-w-[2rem] h-6 px-2 mx-0.5 text-xs font-medium text-muted-foreground bg-muted/50 rounded border border-border/50 align-middle"
                title={`Citation [${part.num}] - Reference not available`}
              >
                <span className="font-semibold">[{part.num}]</span>
                <span className="hidden sm:inline text-[0.65rem] opacity-70">N/A</span>
              </span>
            );
          }
          
          // Truncate chunk text for tooltip (max 300 chars)
          const chunkPreview = ref.chunk_text.length > 300 
            ? ref.chunk_text.substring(0, 300) + '...' 
            : ref.chunk_text;
          
          // Create a more detailed title with source info
          const pageInfo = ref.page_number 
            ? ` (Page ${ref.page_number}${ref.page_number_source === 'estimated' ? ' ~estimated' : ref.page_number_source === 'pdf_search' ? ' ✓verified' : ''})`
            : '';
          const sourceInfo = `${ref.pdf_title}${pageInfo}${ref.date ? ` - ${ref.date}` : ''}${ref.retrieved_at ? ` | Retrieved: ${formatRetrievalTime(ref.retrieved_at)}` : ''}`;
          
          return (
            <span
              key={index}
              className="relative group inline-block"
            >
              <a
                href={`#ref-${messageId || 'default'}-${part.refIndex}`}
                onClick={(e) => {
                  e.preventDefault();
                  // Small delay to ensure DOM is ready
                  setTimeout(() => {
                    onCitationClick(part.refIndex);
                  }, 50);
                }}
                className="inline-flex items-center gap-1 min-w-[2rem] h-6 px-2 mx-0.5 text-xs font-medium text-primary bg-primary/10 hover:bg-primary/20 rounded border border-primary/20 hover:border-primary/40 transition-colors cursor-pointer no-underline align-middle"
                title={`Click to jump to source [${part.num}]`}
              >
                <span className="font-semibold">[{part.num}]</span>
                <span className="hidden sm:inline text-[0.65rem] opacity-70 truncate max-w-[120px]">
                  {ref.pdf_title.length > 20 ? ref.pdf_title.substring(0, 20) + '...' : ref.pdf_title}
                </span>
              </a>
              
              {/* Hover tooltip with document text */}
              <div className="absolute left-0 bottom-full mb-2 w-80 max-w-[90vw] sm:max-w-[400px] p-3 bg-popover border border-border rounded-lg shadow-xl opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 z-50 pointer-events-none">
                <div className="space-y-2">
                  <div className="font-semibold text-sm text-foreground border-b border-border pb-1.5">
                    {sourceInfo}
                  </div>
                  <div className="text-xs text-muted-foreground leading-relaxed max-h-48 overflow-y-auto scrollbar-thin scrollbar-thumb-border scrollbar-track-transparent">
                    {chunkPreview}
                  </div>
                  <div className="text-xs text-muted-foreground pt-1.5 border-t border-border flex items-center justify-between flex-wrap gap-1">
                    {ref.similarity_score && (
                      <span>Relevance: {(ref.similarity_score * 100).toFixed(1)}%</span>
                    )}
                    <div className="flex items-center gap-2">
                      {ref.source && <span className="text-[0.65rem] opacity-70">• {ref.source}</span>}
                      {ref.retrieved_at && (
                        <span className="text-[0.65rem] opacity-70" title={new Date(ref.retrieved_at).toLocaleString()}>
                          • Retrieved: {formatRetrievalTime(ref.retrieved_at)}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
                {/* Arrow pointer */}
                <div className="absolute top-full left-4 w-0 h-0 border-l-4 border-r-4 border-t-4 border-transparent border-t-popover"></div>
              </div>
            </span>
          );
        }
      })}
    </p>
  );
}

export function ChatMessage({ 
  question, 
  answer, 
  references, 
  isLoading, 
  messageId,
  onFeedback,
  initialFeedback,
  citationMap,
  responseTimeMs
}: ChatMessageProps) {
  const [feedback, setFeedback] = useState<'good' | 'bad' | null>(initialFeedback || null);
  const [copied, setCopied] = useState(false);
  const [pageLookups, setPageLookups] = useState<{ [key: number]: { loading?: boolean; pageNumber?: number; pageSource?: string; error?: string } }>({});

  const handleFeedback = (type: 'good' | 'bad') => {
    const newFeedback = feedback === type ? null : type;
    setFeedback(newFeedback);
    if (messageId && onFeedback) {
      onFeedback(messageId, newFeedback);
    }
  };

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(answer);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  const scrollToReference = (refIndex: number) => {
    // Use a more robust ID lookup that handles both messageId and default cases
    const elementId = `ref-${messageId || 'default'}-${refIndex}`;
    
    // Try multiple times with slight delay to handle async rendering
    const attemptScroll = (attempt = 0) => {
      const refElement = document.getElementById(elementId);
      
      if (refElement) {
        try {
          // Find the ScrollArea viewport (Radix UI ScrollArea)
          const scrollAreaViewport = refElement.closest('[data-radix-scroll-area-viewport]') as HTMLElement;
          
          if (scrollAreaViewport) {
            // Calculate scroll position within the ScrollArea
            const elementRect = refElement.getBoundingClientRect();
            const viewportRect = scrollAreaViewport.getBoundingClientRect();
            
            // Calculate the offset needed to center the element
            const elementTop = refElement.offsetTop;
            const elementHeight = refElement.offsetHeight;
            const viewportHeight = viewportRect.height;
            
            // Center the element in the viewport
            const scrollTop = elementTop - (viewportHeight / 2) + (elementHeight / 2);
            
            // Scroll within the ScrollArea
            scrollAreaViewport.scrollTo({
              top: Math.max(0, scrollTop),
              behavior: 'smooth'
            });
          } else {
            // Fallback: use standard scrollIntoView if not in ScrollArea
            refElement.scrollIntoView({ 
              behavior: 'smooth', 
              block: 'center', 
              inline: 'nearest' 
            });
          }
          
          // Highlight the reference briefly
          refElement.classList.add('ring-2', 'ring-primary', 'ring-offset-2');
          setTimeout(() => {
            refElement.classList.remove('ring-2', 'ring-primary', 'ring-offset-2');
          }, 2000);
        } catch (error) {
          console.error('Error scrolling to reference:', error);
          // Fallback: just highlight the element
          refElement.classList.add('ring-2', 'ring-primary', 'ring-offset-2');
          setTimeout(() => {
            refElement.classList.remove('ring-2', 'ring-primary', 'ring-offset-2');
          }, 2000);
        }
      } else if (attempt < 3) {
        // Retry if element not found (might still be rendering)
        setTimeout(() => attemptScroll(attempt + 1), 100 * (attempt + 1));
      } else {
        // Log warning after all attempts failed
        console.warn(`Reference element not found after ${attempt + 1} attempts: ${elementId}`);
        const availableIds = Array.from(document.querySelectorAll('[id^="ref-"]')).map(el => el.id);
        if (availableIds.length > 0) {
          console.warn('Available reference IDs:', availableIds);
        }
      }
    };
    
    // Start scrolling attempt
    attemptScroll();
  };

  return (
    <div className="w-full max-w-4xl mx-auto space-y-4 sm:space-y-6 px-2 sm:px-0">
      {/* Question */}
      <div className="flex gap-2 sm:gap-4">
        <div className="flex-shrink-0 w-7 h-7 sm:w-8 sm:h-8 rounded-full bg-primary/10 flex items-center justify-center text-xs sm:text-sm font-medium">
          Q
        </div>
        <div className="flex-1 pt-1 min-w-0">
          <p className="text-foreground text-base sm:text-lg leading-relaxed break-words">{question}</p>
        </div>
      </div>

      {/* Answer */}
      <div className="flex gap-2 sm:gap-4">
        <div className="flex-shrink-0 w-7 h-7 sm:w-8 sm:h-8 rounded-full bg-primary flex items-center justify-center text-xs sm:text-sm font-medium text-primary-foreground">
          A
        </div>
        <div className="flex-1 space-y-3 sm:space-y-4 min-w-0">
          {isLoading ? (
            <div className="space-y-2">
              <div className="h-4 bg-muted rounded w-3/4 animate-pulse" />
              <div className="h-4 bg-muted rounded w-5/6 animate-pulse" />
              <div className="h-4 bg-muted rounded w-4/6 animate-pulse" />
            </div>
          ) : (
            <>
              <div className="prose prose-sm max-w-none">
                <AnswerWithCitations 
                  answer={answer} 
                  references={references}
                  citationMap={citationMap}
                  messageId={messageId}
                  onCitationClick={scrollToReference}
                />
              </div>
              
              {/* Response Time and Feedback Buttons */}
              <div className="flex items-center justify-between gap-2 pt-2">
                {responseTimeMs !== undefined && responseTimeMs !== null && (
                  <div className="text-xs text-muted-foreground flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    <span>Response time: {formatDuration(responseTimeMs)}</span>
                  </div>
                )}
                <div className="flex items-center gap-2 ml-auto">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handleFeedback('good')}
                  className={cn(
                    "h-8 px-3 text-xs",
                    feedback === 'good' && "bg-green-500/10 text-green-600 dark:text-green-400"
                  )}
                >
                  <ThumbsUp className={cn("w-3 h-3 mr-1.5", feedback === 'good' && "fill-current")} />
                  Good
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handleFeedback('bad')}
                  className={cn(
                    "h-8 px-3 text-xs",
                    feedback === 'bad' && "bg-red-500/10 text-red-600 dark:text-red-400"
                  )}
                >
                  <ThumbsDown className={cn("w-3 h-3 mr-1.5", feedback === 'bad' && "fill-current")} />
                  Not Good
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleCopy}
                  className="h-8 px-3 text-xs"
                >
                  {copied ? (
                    <>
                      <Check className="w-3 h-3 mr-1.5" />
                      Copied
                    </>
                  ) : (
                    <>
                      <Copy className="w-3 h-3 mr-1.5" />
                      Copy
                    </>
                  )}
                </Button>
                </div>
              </div>
            </>
          )}

          {/* References */}
          {!isLoading && references.length > 0 && (
            <div className="mt-4 sm:mt-6 pt-4 sm:pt-6 border-t border-border">
              <h3 className="text-xs sm:text-sm font-semibold text-muted-foreground mb-2 sm:mb-3 flex items-center gap-2">
                <FileText className="w-3 h-3 sm:w-4 sm:h-4" />
                Sources ({references.length})
              </h3>
              <ScrollArea className="h-[250px] sm:h-[300px]">
                <div className="space-y-3 pr-4">
                  {references.map((ref, index) => {
                    // Ensure consistent ID generation
                    const refId = `ref-${messageId || 'default'}-${index}`;
                    return (
                    <div
                      key={`${messageId || 'default'}-${index}`}
                      id={refId}
                      className="p-3 rounded-lg border border-border bg-card hover:bg-accent/50 transition-colors scroll-mt-4"
                      data-ref-index={index}
                    >
                      <div className="flex items-start justify-between gap-2 mb-2">
                        <h4 className="text-sm font-medium text-foreground line-clamp-2">
                          {ref.pdf_title}
                        </h4>
                        {ref.pdf_url && (
                          <a
                            href={ref.pdf_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="flex-shrink-0 text-muted-foreground hover:text-foreground transition-colors"
                          >
                            <ExternalLink className="w-4 h-4" />
                          </a>
                        )}
                      </div>
                      <p className="text-xs text-muted-foreground line-clamp-2 mb-2">
                        {ref.chunk_text}
                      </p>
                      <div className="flex items-center gap-3 text-xs text-muted-foreground flex-wrap">
                        <span>Score: {(ref.similarity_score * 100).toFixed(1)}%</span>
                        {(() => {
                          const lookup = pageLookups[index];
                          const displayPageNumber = lookup?.pageNumber ?? ref.page_number;
                          const displayPageSource = lookup?.pageSource ?? ref.page_number_source;
                          const isLoadingPage = lookup?.loading;
                          
                          if (displayPageNumber && ref.pdf_url) {
                            return (
                              <a
                                href={`${ref.pdf_url}#page=${displayPageNumber}`}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="inline-flex items-center gap-1 hover:text-primary hover:underline transition-colors cursor-pointer font-medium"
                                title={`Jump to page ${displayPageNumber} in PDF${displayPageSource === 'estimated' ? ' (estimated)' : displayPageSource === 'pdf_search' ? ' (found in PDF)' : ''}`}
                              >
                                <span>•</span>
                                <LinkIcon className="w-3 h-3" />
                                <span>Page {displayPageNumber}</span>
                                {displayPageSource === 'estimated' && (
                                  <span className="text-[0.6rem] opacity-60" title="Page number is estimated">~</span>
                                )}
                                {displayPageSource === 'pdf_search' && (
                                  <span className="text-[0.6rem] opacity-60" title="Page number verified in PDF">✓</span>
                                )}
                              </a>
                            );
                          } else if (displayPageNumber) {
                            return (
                              <span className="inline-flex items-center gap-1">
                                <span>•</span>
                                <span>Page {displayPageNumber}</span>
                                {displayPageSource === 'estimated' && (
                                  <span className="text-[0.6rem] opacity-60" title="Page number is estimated">~</span>
                                )}
                              </span>
                            );
                          } else if (ref.pdf_url && !isLoadingPage) {
                            // Page number not found - show message (automatic lookup should have tried)
                            return (
                              <span className="inline-flex items-center gap-1 text-muted-foreground text-xs">
                                <span>•</span>
                                <span>Page not found</span>
                              </span>
                            );
                          } else if (isLoadingPage) {
                            return (
                              <span className="inline-flex items-center gap-1 text-muted-foreground">
                                <span>•</span>
                                <Loader2 className="w-3 h-3 animate-spin" />
                                <span>Finding page...</span>
                              </span>
                            );
                          }
                          return null;
                        })()}
                        {ref.source && <span>• {ref.source}</span>}
                        {ref.date && <span>• Doc: {ref.date}</span>}
                        {ref.retrieved_at && (
                          <span className="text-[0.65rem] opacity-70" title={`Retrieved at ${new Date(ref.retrieved_at).toLocaleString()}`}>
                            • Retrieved: {formatRetrievalTime(ref.retrieved_at)}
                          </span>
                        )}
                      </div>
                    </div>
                    );
                  })}
                </div>
              </ScrollArea>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
