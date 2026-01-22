'use client';

import { useState, KeyboardEvent, useRef, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Send, Loader2 } from 'lucide-react';

interface ChatInputProps {
  onSend: (message: string) => void;
  isLoading?: boolean;
  disabled?: boolean;
}

export function ChatInput({ onSend, isLoading, disabled }: ChatInputProps) {
  const [message, setMessage] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`;
    }
  }, [message]);

  const handleSend = () => {
    if (message.trim() && !isLoading && !disabled) {
      onSend(message.trim());
      setMessage('');
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="w-full max-w-4xl mx-auto">
      <div className="relative flex items-end gap-2 p-3 sm:p-4 border border-border rounded-xl sm:rounded-2xl bg-background shadow-sm focus-within:ring-2 focus-within:ring-ring focus-within:border-transparent">
        <textarea
          ref={textareaRef}
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask anything about Islamic finance..."
          disabled={isLoading || disabled}
          rows={1}
          className="flex-1 resize-none border-0 bg-transparent focus:outline-none focus:ring-0 placeholder:text-muted-foreground text-foreground text-sm sm:text-base min-h-[24px] max-h-[200px] overflow-y-auto"
        />
        <Button
          onClick={handleSend}
          disabled={!message.trim() || isLoading || disabled}
          size="icon"
          className="flex-shrink-0 h-8 w-8 sm:h-9 sm:w-9 rounded-lg"
        >
          {isLoading ? (
            <Loader2 className="h-3.5 w-3.5 sm:h-4 sm:w-4 animate-spin" />
          ) : (
            <Send className="h-3.5 w-3.5 sm:h-4 sm:w-4" />
          )}
        </Button>
      </div>
      <p className="text-xs text-muted-foreground mt-1.5 sm:mt-2 text-center hidden sm:block">
        Press Enter to send, Shift+Enter for new line
      </p>
    </div>
  );
}
