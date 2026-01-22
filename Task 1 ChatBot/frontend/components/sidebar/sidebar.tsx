'use client';

import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import { Checkbox } from '@/components/ui/checkbox';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
} from '@/components/ui/dropdown-menu';
import {
  MessageSquare,
  Settings,
  FileText,
  Building2,
  Globe,
  Sparkles,
  X,
  BarChart3,
  History,
  ChevronDown,
  Database,
} from 'lucide-react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';

export interface ChatHistory {
  id: string;
  title: string;
  timestamp: number;
}

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
  chatHistory: ChatHistory[];
  selectedChatId: string | null;
  onSelectChat: (id: string | null) => void;
  onNewChat: () => void;
  collections: string[];
  selectedCollections: string[];
  onCollectionsChange: (collections: string[]) => void;
}

const collectionLabels: Record<string, string> = {
  all: 'All Collections',
  bnm_pdfs: 'Bank Negara Malaysia',
  iifa_resolutions: 'IIFA Resolutions',
  sc_resolutions: 'SC Resolutions',
};

const collectionIcons: Record<string, React.ReactNode> = {
  all: <Globe className="w-4 h-4" />,
  bnm_pdfs: <Building2 className="w-4 h-4" />,
  iifa_resolutions: <FileText className="w-4 h-4" />,
  sc_resolutions: <FileText className="w-4 h-4" />,
};

export function Sidebar({
  isOpen,
  onClose,
  chatHistory,
  selectedChatId,
  onSelectChat,
  onNewChat,
  collections,
  selectedCollections,
  onCollectionsChange,
}: SidebarProps) {
  const [isMobile, setIsMobile] = useState(false);
  const pathname = usePathname();

  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768);
    };
    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  const handleCollectionToggle = (collection: string) => {
    if (collection === 'all') {
      onCollectionsChange(['all']);
    } else {
      const newCollections = selectedCollections.includes(collection)
        ? selectedCollections.filter((c) => c !== collection)
        : [...selectedCollections.filter((c) => c !== 'all'), collection];
      onCollectionsChange(newCollections.length > 0 ? newCollections : ['all']);
    }
  };

  const formatDate = (timestamp: number) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));

    if (days === 0) return 'Today';
    if (days === 1) return 'Yesterday';
    if (days < 7) return `${days} days ago`;
    return date.toLocaleDateString();
  };

  return (
    <>
      {/* Overlay for mobile */}
      {isOpen && isMobile && (
        <div
          className="fixed inset-0 bg-black/50 z-40 md:hidden"
          onClick={onClose}
        />
      )}

      {/* Sidebar */}
      <aside
      className={cn(
        'fixed left-0 top-0 h-full w-64 bg-background border-r border-border z-50 transform transition-transform duration-300 ease-in-out',
        'md:static md:translate-x-0', // Always visible on desktop
        isOpen ? 'translate-x-0' : '-translate-x-full',
        'flex flex-col'
      )}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-border">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center">
              <Sparkles className="w-5 h-5 text-primary-foreground" />
            </div>
            <span className="font-semibold text-foreground">Neo AI</span>
          </div>
          <Button
            variant="ghost"
            size="icon"
            onClick={onClose}
            className="md:hidden h-8 w-8"
          >
            <X className="h-4 w-4" />
          </Button>
        </div>

        <ScrollArea className="flex-1">
          <div className="p-4 space-y-6">
              {/* Navigation */}
              <div className="space-y-1">
                <Link href="/chat" className="block">
                  <Button
                    variant={pathname === '/chat' ? "default" : "ghost"}
                    className={cn(
                      "w-full justify-start gap-2",
                      pathname === '/chat' && "bg-accent text-accent-foreground"
                    )}
                    onClick={() => {
                      if (isMobile) onClose();
                    }}
                  >
                    <MessageSquare className="w-4 h-4" />
                    Chat
                  </Button>
                </Link>
              </div>

            {/* Chat History */}
            {chatHistory.length > 0 && (
              <div className="space-y-2">
                <div className="flex items-center justify-between px-2">
                  <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                    Recent
                  </h3>
                  {chatHistory.length > 2 && (
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-6 px-2 text-xs text-muted-foreground hover:text-foreground"
                        >
                          <History className="w-3 h-3 mr-1" />
                          History
                          <ChevronDown className="w-3 h-3 ml-1" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end" className="w-64 max-h-[400px] overflow-y-auto">
                        <div className="space-y-1">
                          {chatHistory.map((chat) => (
                            <DropdownMenuItem
                              key={chat.id}
                              onClick={() => {
                                onSelectChat(chat.id);
                                if (isMobile) onClose();
                              }}
                              className={cn(
                                "cursor-pointer",
                                selectedChatId === chat.id && "bg-accent"
                              )}
                            >
                              <MessageSquare className="w-4 h-4 mr-2 flex-shrink-0" />
                              <div className="flex-1 min-w-0">
                                <div className="truncate text-sm">{chat.title}</div>
                                <div className="text-xs text-muted-foreground">
                                  {formatDate(chat.timestamp)}
                                </div>
                              </div>
                            </DropdownMenuItem>
                          ))}
                        </div>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  )}
                </div>
                <div className="space-y-1">
                  {chatHistory.slice(0, 2).map((chat) => (
                    <button
                      key={chat.id}
                      onClick={() => onSelectChat(chat.id)}
                      className={cn(
                        'w-full text-left px-3 py-2 rounded-lg text-sm transition-colors flex items-center gap-2 group',
                        selectedChatId === chat.id
                          ? 'bg-accent text-accent-foreground'
                          : 'hover:bg-accent/50 text-foreground'
                      )}
                    >
                      <MessageSquare className="w-4 h-4 flex-shrink-0" />
                      <div className="flex-1 min-w-0">
                        <div className="truncate">{chat.title}</div>
                        <div className="text-xs text-muted-foreground mt-0.5">
                          {formatDate(chat.timestamp)}
                        </div>
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            )}

            <Separator />

            {/* Collections */}
            <div className="space-y-2">
              <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider px-2">
                Sources
              </h3>
              <div className="space-y-2">
                {collections.map((collection) => {
                  const isSelected = selectedCollections.includes(collection);
                  return (
                    <label
                      key={collection}
                      className={cn(
                        'flex items-center gap-2 px-3 py-2 rounded-lg cursor-pointer transition-colors',
                        isSelected
                          ? 'bg-accent/50'
                          : 'hover:bg-accent/30'
                      )}
                    >
                      <Checkbox
                        checked={isSelected}
                        onCheckedChange={() => handleCollectionToggle(collection)}
                      />
                      <div className="flex items-center gap-2 flex-1 min-w-0">
                        {collectionIcons[collection] || <FileText className="w-4 h-4" />}
                        <span className="text-sm text-foreground truncate">
                          {collectionLabels[collection] || collection}
                        </span>
                      </div>
                    </label>
                  );
                })}
              </div>
            </div>
          </div>
        </ScrollArea>

        {/* Footer */}
        <div className="p-4 border-t border-border space-y-1">
          <Link href="/dashboard" className="block">
            <Button
              variant="ghost"
              className={cn(
                "w-full justify-start gap-2",
                pathname === '/dashboard' && "bg-accent text-accent-foreground"
              )}
              onClick={() => {
                if (isMobile) onClose();
              }}
            >
              <BarChart3 className="w-4 h-4" />
              Dashboard
            </Button>
          </Link>
          <Link href="/scraper" className="block">
            <Button
              variant="ghost"
              className={cn(
                "w-full justify-start gap-2",
                pathname === '/scraper' && "bg-accent text-accent-foreground"
              )}
              onClick={() => {
                if (isMobile) onClose();
              }}
            >
              <Database className="w-4 h-4" />
              Web Scraper
            </Button>
          </Link>
          <Link href="/settings" className="block">
            <Button
              variant="ghost"
              className={cn(
                "w-full justify-start gap-2",
                pathname === '/settings' && "bg-accent text-accent-foreground"
              )}
              onClick={() => {
                if (isMobile) onClose();
              }}
            >
              <Settings className="w-4 h-4" />
              Settings
            </Button>
          </Link>
        </div>
      </aside>
    </>
  );
}
