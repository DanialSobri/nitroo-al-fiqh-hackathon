'use client';

import { useState, useEffect, useRef, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import { ChatMessage } from '@/components/chat/chat-message';
import { ChatInput } from '@/components/chat/chat-input';
import { askQuestion, QuestionResponse, getCollections, getRecentConversations, getSessionConversations } from '@/lib/api';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Sidebar, ChatHistory } from '@/components/sidebar/sidebar';
import { SidebarToggle } from '@/components/sidebar/sidebar-toggle';
import { ThemeToggle } from '@/components/theme-toggle';
import { Sparkles, Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';

interface Message extends QuestionResponse {
  id: string;
  feedback?: 'good' | 'bad' | null;
  response_time_ms?: number;
}

function ChatPageContent() {
  const searchParams = useSearchParams();
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
  const hasAutoLoadedRef = useRef(false);
  const isNewChatRef = useRef(false); // Track if user explicitly created a new chat

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
      
      // Convert to ChatHistory format
      const history: ChatHistory[] = sessions.map(session => ({
        id: session.session_id,
        title: session.title,
        timestamp: new Date(session.timestamp).getTime()
      }));
      
      // Merge with local storage history (prefer backend)
      setChatHistory(history);
      localStorage.setItem('chatHistory', JSON.stringify(history));
      
      return history;
    } catch (err) {
      console.error('Failed to load chat history from backend:', err);
      // Fallback to local storage
      const savedHistory = localStorage.getItem('chatHistory');
      if (savedHistory) {
        try {
          const parsed = JSON.parse(savedHistory);
          setChatHistory(parsed);
          return parsed;
        } catch (e) {
          console.error('Failed to load local chat history:', e);
        }
      }
      return [];
    }
  };

  // Load chat history from localStorage and backend
  useEffect(() => {
    // Load available collections from API
    getCollections()
      .then((cols) => {
        setAvailableCollections(['all', ...cols]);
      })
      .catch((err) => {
        console.error('Failed to load collections:', err);
      });
    
    // Load chat history
    loadChatHistoryFromBackend();
  }, []);

  // Handle URL parameter for session loading
  useEffect(() => {
    const sessionParam = searchParams?.get('session');
    if (sessionParam && chatHistory.length > 0 && !currentChatId && !hasAutoLoadedRef.current && !isNewChatRef.current) {
      // Check if session exists in history
      const sessionExists = chatHistory.some(h => h.id === sessionParam);
      if (sessionExists) {
        hasAutoLoadedRef.current = true;
        handleSelectChat(sessionParam);
      }
    }
  }, [searchParams, chatHistory, currentChatId]);

  // Auto-load most recent conversation when history is loaded and no messages are displayed
  // BUT NOT when user explicitly created a new chat
  useEffect(() => {
    if (chatHistory.length > 0 && messages.length === 0 && !currentChatId && !hasAutoLoadedRef.current && !searchParams?.get('session') && !isNewChatRef.current) {
      hasAutoLoadedRef.current = true;
      const mostRecentSession = chatHistory[0]; // Already sorted by timestamp (most recent first)
      handleSelectChat(mostRecentSession.id);
    }
  }, [chatHistory, messages.length, currentChatId, searchParams]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const handleNewChat = () => {
    // Set flag to prevent auto-loading
    isNewChatRef.current = true;
    hasAutoLoadedRef.current = true; // Set this to prevent auto-load effect
    
    setMessages([]);
    setCurrentChatId(null);
    setError(null);
    // Clear any pending state
    setIsLoading(false);
    
    // Clear URL parameters if present
    if (window.history.replaceState) {
      window.history.replaceState({}, '', '/chat');
    }
    
    if (window.innerWidth < 768) { // Close sidebar on mobile after new chat
      setSidebarOpen(false);
    }
    
    // Reset the flag after state updates complete
    // This prevents auto-load from triggering
    setTimeout(() => {
      isNewChatRef.current = false;
      // Keep hasAutoLoadedRef as true to prevent auto-loading
      // It will be reset when user manually selects a chat or sends a message
    }, 500);
    
    // Reload chat history to ensure it's up to date (but don't auto-load)
    loadChatHistoryFromBackend();
  };

  const handleSelectChat = async (chatId: string | null) => {
    if (!chatId) {
      handleNewChat();
      return;
    }

    // Reset flags when manually selecting a chat
    isNewChatRef.current = false;
    hasAutoLoadedRef.current = true; // Mark as loaded to prevent auto-load

    try {
      // Try to load from backend first
      const { conversations } = await getSessionConversations(chatId);
      
      if (conversations && conversations.length > 0) {
        // Convert to Message format
        const messages: Message[] = conversations.map((conv, idx) => ({
          id: conv.conversation_id || `msg_${idx}`,
          question: conv.question,
          answer: conv.answer,
          references: [],
          total_references_found: 0,
          collections_searched: [],
          citation_map: null
        }));
        
        setMessages(messages);
        setCurrentChatId(chatId);
        
        // Update chat history
        const updatedHistory = chatHistory.map(h => 
          h.id === chatId ? { ...h, timestamp: Date.now() } : h
        );
        setChatHistory(updatedHistory);
        localStorage.setItem('chatHistory', JSON.stringify(updatedHistory));
        
        if (window.innerWidth < 768) {
          setSidebarOpen(false);
        }
      } else {
        // Fallback to local storage
        const savedChats = localStorage.getItem('chatHistory');
        if (savedChats) {
          const history = JSON.parse(savedChats);
          const chat = history.find((h: ChatHistory) => h.id === chatId);
          if (chat) {
            const savedMessages = localStorage.getItem(`chat_${chatId}`);
            if (savedMessages) {
              setMessages(JSON.parse(savedMessages));
              setCurrentChatId(chatId);
              if (window.innerWidth < 768) {
                setSidebarOpen(false);
              }
            }
          }
        }
      }
    } catch (err) {
      console.error('Failed to load chat from backend:', err);
      // Fallback to local storage
      const savedChats = localStorage.getItem('chatHistory');
      if (savedChats) {
        try {
          const history = JSON.parse(savedChats);
          const chat = history.find((h: ChatHistory) => h.id === chatId);
          if (chat) {
            const savedMessages = localStorage.getItem(`chat_${chatId}`);
            if (savedMessages) {
              setMessages(JSON.parse(savedMessages));
              setCurrentChatId(chatId);
              if (window.innerWidth < 768) {
                setSidebarOpen(false);
              }
            }
          }
        } catch (e) {
          console.error('Failed to load chat:', e);
        }
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

    // Get user ID and session ID
    const userId = getUserId();
    let chatId = currentChatId;
    if (!chatId) {
      chatId = `chat_${Date.now()}`;
      setCurrentChatId(chatId);
      // Reset flags when starting a new conversation
      isNewChatRef.current = false;
      hasAutoLoadedRef.current = true;
      
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

      const sessionId = chatId;
      
      const response = await askQuestion({
        question,
        collections: collectionsToUse,
        max_results: savedMaxResults,
        min_score: savedMinScore,
        user_id: userId,
        session_id: sessionId,
      });

      // Replace the temp message with the actual response using functional update
      setMessages((prev) => {
        const finalMessages = prev.map((msg) =>
          msg.id === messageId
            ? { ...response, id: messageId, feedback: null, citation_map: response.citation_map, response_time_ms: response.response_time_ms }
            : msg
        );
        
        // Save to localStorage
        if (chatId) {
          localStorage.setItem(`chat_${chatId}`, JSON.stringify(finalMessages));
        }
        
        // Reload chat history from backend to get updated list
        loadChatHistoryFromBackend();
        
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
                      'What if I sell liquor, how to make it shariah compliant',
                      'Is credit card shariah compliance?',
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
                      citationMap={message.citation_map}
                      responseTimeMs={message.response_time_ms}
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

export default function ChatPage() {
  return (
    <Suspense fallback={
      <div className="flex items-center justify-center h-screen">
        <div className="text-center space-y-4">
          <Loader2 className="w-8 h-8 animate-spin mx-auto text-primary" />
          <p className="text-muted-foreground">Loading chat...</p>
        </div>
      </div>
    }>
      <ChatPageContent />
    </Suspense>
  );
}
