'use client';

import { useState } from 'react';
import { SourceReference } from '@/lib/api';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Button } from '@/components/ui/button';
import { FileText, ExternalLink, ThumbsUp, ThumbsDown, Copy, Check } from 'lucide-react';
import { cn } from '@/lib/utils';

interface ChatMessageProps {
  question: string;
  answer: string;
  references: SourceReference[];
  isLoading?: boolean;
  messageId?: string;
  onFeedback?: (messageId: string, feedback: 'good' | 'bad' | null) => void;
  initialFeedback?: 'good' | 'bad' | null;
}

export function ChatMessage({ 
  question, 
  answer, 
  references, 
  isLoading, 
  messageId,
  onFeedback,
  initialFeedback 
}: ChatMessageProps) {
  const [feedback, setFeedback] = useState<'good' | 'bad' | null>(initialFeedback || null);
  const [copied, setCopied] = useState(false);

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
                <p className="text-foreground/90 leading-relaxed whitespace-pre-wrap">{answer}</p>
              </div>
              
              {/* Feedback Buttons */}
              <div className="flex items-center gap-2 pt-2">
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
                  {references.map((ref, index) => (
                    <div
                      key={index}
                      className="p-3 rounded-lg border border-border bg-card hover:bg-accent/50 transition-colors"
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
                      <div className="flex items-center gap-3 text-xs text-muted-foreground">
                        <span>Score: {(ref.similarity_score * 100).toFixed(1)}%</span>
                        {ref.source && <span>• {ref.source}</span>}
                        {ref.date && <span>• {ref.date}</span>}
                      </div>
                    </div>
                  ))}
                </div>
              </ScrollArea>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
