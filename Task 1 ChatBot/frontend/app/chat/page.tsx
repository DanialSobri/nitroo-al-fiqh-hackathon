'use client';

import { useState, useEffect, useRef } from 'react';
import { ChatMessage } from '@/components/chat/chat-message';
import { ChatInput } from '@/components/chat/chat-input';
import { askQuestion, QuestionResponse, getCollections } from '@/lib/api';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Sidebar, ChatHistory } from '@/components/sidebar/sidebar';
import { SidebarToggle } from '@/components/sidebar/sidebar-toggle';
import { ThemeToggle } from '@/components/theme-toggle';
import { Sparkles } from 'lucide-react';
import { cn } from '@/lib/utils';

interface Message extends QuestionResponse {
  id: string;
  feedback?: 'good' | 'bad' | null;
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(true); // Open by default on desktop
  const [chatHistory, setChatHistory] = useState<ChatHistory[]>([]);
  const [currentChatId, setCurrentChatId] = useState<string | null>(null);
  const [availableCollections, setAvailableCollections] = useState<string[]>(['all', 'bnm_pdfs', 'iifa_resolutions', 'sc_resolutions']);
  const [selectedCollections, setSelectedCollections] = useState<string[]>(['all']);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const scrollAreaRef = useRef<HTMLDivElement>(null);

  // Load chat history from localStorage
  useEffect(() => {
    const savedHistory = localStorage.getItem('chatHistory');
    if (savedHistory) {
      try {
        setChatHistory(JSON.parse(savedHistory));
      } catch (e) {
        console.error('Failed to load chat history:', e);
      }
    }

    // Load available collections from API
    getCollections()
      .then((cols) => {
        setAvailableCollections(['all', ...cols]);
      })
      .catch((err) => {
        console.error('Failed to load collections:', err);
      });
  }, []);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const handleNewChat = () => {
    setMessages([]);
    setCurrentChatId(null);
    setError(null);
    if (window.innerWidth < 768) { // Close sidebar on mobile after new chat
      setSidebarOpen(false);
    }
  };

  const handleSelectChat = (chatId: string | null) => {
    if (!chatId) {
      handleNewChat();
      return;
    }

    // Load chat from history
    const savedChats = localStorage.getItem('chatHistory');
    if (savedChats) {
      try {
        const history = JSON.parse(savedChats);
        const chat = history.find((h: ChatHistory) => h.id === chatId);
        if (chat) {
          // Load messages for this chat
          const savedMessages = localStorage.getItem(`chat_${chatId}`);
          if (savedMessages) {
            setMessages(JSON.parse(savedMessages));
            setCurrentChatId(chatId);
            if (window.innerWidth < 768) { // Close sidebar on mobile after selecting chat
              setSidebarOpen(false);
            }
          }
        }
      } catch (e) {
        console.error('Failed to load chat:', e);
      }
    }
  };

  const handleSend = async (question: string) => {
    setError(null);
    setIsLoading(true);

    // Helper function to truncate title with ellipsis
    const truncateTitle = (text: string, maxLength: number = 25): string => {
      const trimmed = text.trim();
      if (trimmed.length <= maxLength) {
        return trimmed;
      }
      return trimmed.substring(0, maxLength) + '...';
    };

    // Create new chat if no current chat
    let chatId = currentChatId;
    if (!chatId) {
      chatId = Date.now().toString();
      setCurrentChatId(chatId);
      
      // Add to history
      const newHistory: ChatHistory = {
        id: chatId,
        title: truncateTitle(question),
        timestamp: Date.now(),
      };
      setChatHistory((prev) => {
        const updated = [newHistory, ...prev].slice(0, 20); // Keep last 20
        localStorage.setItem('chatHistory', JSON.stringify(updated));
        return updated;
      });
    }

    const messageId = Date.now().toString();
    const tempMessage: Message = {
      id: messageId,
      question,
      answer: '',
      references: [],
      total_references_found: 0,
      collections_searched: [],
    };

    setMessages((prev) => [...prev, tempMessage]);

    try {
      // Load settings from localStorage
      const savedMaxResults = parseInt(localStorage.getItem('maxResults') || '5', 10);
      const savedMinScore = parseFloat(localStorage.getItem('minScore') || '0.5');
      const savedDefaultCollections = JSON.parse(localStorage.getItem('defaultCollections') || '["all"]');
      
      // Use saved collections if none selected, otherwise use selected
      const collectionsToUse = selectedCollections.length > 0 && !selectedCollections.includes('all') 
        ? selectedCollections 
        : savedDefaultCollections;

      const response = await askQuestion({
        question,
        collections: collectionsToUse,
        max_results: savedMaxResults,
        min_score: savedMinScore,
      });

      // Replace the temp message with the actual response using functional update
      setMessages((prev) => {
        const finalMessages = prev.map((msg) =>
          msg.id === messageId
            ? { ...response, id: messageId, feedback: null }
            : msg
        );
        
        // Save to localStorage
        if (chatId) {
          localStorage.setItem(`chat_${chatId}`, JSON.stringify(finalMessages));
        }
        
        return finalMessages;
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === messageId
            ? {
                ...msg,
                answer: `Error: ${err instanceof Error ? err.message : 'Failed to get response'}`,
              }
            : msg
        )
      );
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex h-screen bg-background">
      {/* Sidebar */}
      <Sidebar
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        chatHistory={chatHistory}
        selectedChatId={currentChatId}
        onSelectChat={handleSelectChat}
        onNewChat={handleNewChat}
        collections={availableCollections}
        selectedCollections={selectedCollections}
        onCollectionsChange={setSelectedCollections}
      />

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
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
                  <h1 className="text-lg sm:text-xl font-semibold text-foreground truncate">Neo AI</h1>
                  <p className="text-xs text-muted-foreground hidden sm:block">Next‑Gen Optimized Advisor, driven by Agentic AI</p>
                </div>
              </div>
              <ThemeToggle />
            </div>
          </div>
        </header>

        {/* Main Content */}
        <div className="flex-1 overflow-hidden">
          <ScrollArea className="h-full" ref={scrollAreaRef}>
          <div className="container mx-auto px-4 sm:px-6 py-4 sm:py-8">
                   {messages.length === 0 ? (
                     <div className="flex flex-col items-center justify-center h-full min-h-[50vh] sm:min-h-[60vh] text-center space-y-4 px-4">
                       <div className="w-12 h-12 sm:w-16 sm:h-16 rounded-full bg-primary/10 flex items-center justify-center">
                         <Sparkles className="w-6 h-6 sm:w-8 sm:h-8 text-primary" />
                       </div>
                       <div className="space-y-2">
                         <h2 className="text-xl sm:text-2xl font-semibold text-foreground">
                           Ask anything about Islamic Finance
                         </h2>
                         <p className="text-sm sm:text-base text-muted-foreground max-w-md">
                           Get answers based on official documents from trusted sources including 
                           regulatory bodies, financial institutions, and compliance organizations
                         </p>
                       </div>
                       <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 sm:gap-4 mt-6 sm:mt-8 w-full max-w-2xl">
                    {[
                      'What is Shariah non-tolerable income threshold?',
                      'Explain the requirements for sukuk issuance',
                      'What are the Shariah screening criteria?',
                         ].map((example, i) => (
                           <button
                             key={i}
                             onClick={() => handleSend(example)}
                             disabled={isLoading}
                             className="p-3 sm:p-4 text-left rounded-lg border border-border bg-card hover:bg-accent/50 transition-colors text-xs sm:text-sm text-foreground disabled:opacity-50 disabled:cursor-not-allowed"
                           >
                             {example}
                           </button>
                         ))}
                       </div>
                     </div>
                   ) : (
                     <div className="space-y-4 sm:space-y-8 pb-4 sm:pb-8">
                  {messages.map((message, index) => (
                    <ChatMessage
                      key={message.id}
                      question={message.question}
                      answer={message.answer}
                      references={message.references}
                      isLoading={isLoading && index === messages.length - 1 && !message.answer}
                      messageId={message.id}
                      initialFeedback={message.feedback}
                      onFeedback={(messageId, feedback) => {
                        setMessages((prev) => {
                          const updated = prev.map((msg) =>
                            msg.id === messageId ? { ...msg, feedback } : msg
                          );
                          // Save to localStorage
                          if (currentChatId) {
                            localStorage.setItem(`chat_${currentChatId}`, JSON.stringify(updated));
                          }
                          return updated;
                        });
                      }}
                    />
                  ))}
                  <div ref={messagesEndRef} />
                </div>
              )}

              {error && (
                <div className="fixed bottom-20 left-1/2 transform -translate-x-1/2 bg-destructive text-destructive-foreground px-4 py-2 rounded-lg text-sm shadow-lg z-50">
                  {error}
                </div>
              )}
            </div>
          </ScrollArea>
        </div>

               {/* Input Area */}
               <div className="border-t border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
                 <div className="container mx-auto px-4 sm:px-6 py-3 sm:py-4">
                   <ChatInput onSend={handleSend} isLoading={isLoading} />
                 </div>
               </div>
      </div>
    </div>
  );
}
