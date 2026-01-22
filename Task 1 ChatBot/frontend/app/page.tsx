'use client';

import Link from 'next/link';
import { Sparkles, MessageSquare, FileText, Database, BarChart3, ArrowRight, BookOpen, Shield, Search } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { ThemeToggle } from '@/components/theme-toggle';

export default function LandingPage() {
  const features = [
    {
      icon: <FileText className="w-6 h-6" />,
      title: 'BNM Documents',
      description: 'Access official Islamic banking regulations and guidelines from Bank Negara Malaysia',
    },
    {
      icon: <BookOpen className="w-6 h-6" />,
      title: 'IIFA Resolutions',
      description: 'Query resolutions and fatwas from the International Islamic Fiqh Academy (IIFA)',
    },
    {
      icon: <Shield className="w-6 h-6" />,
      title: 'SC Resolutions',
      description: 'Explore Shariah Advisory Council resolutions from Securities Commission Malaysia',
    },
    {
      icon: <Search className="w-6 h-6" />,
      title: 'Source-Backed Answers',
      description: 'Get accurate answers with references to original documents and similarity scores',
    },
    {
      icon: <MessageSquare className="w-6 h-6" />,
      title: 'Real-Time Q&A',
      description: 'Ask questions and receive instant responses powered by advanced RAG technology',
    },
    {
      icon: <Database className="w-6 h-6" />,
      title: 'Vector Search',
      description: 'Leverage semantic search across thousands of document chunks for precise results',
    },
  ];

  return (
    <div className="min-h-screen bg-background flex flex-col">
      {/* Header */}
      <header className="border-b border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 sticky top-0 z-50">
        <div className="container mx-auto px-4 sm:px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center">
                <Sparkles className="w-5 h-5 text-primary-foreground" />
              </div>
              <div>
                <h1 className="text-lg sm:text-xl font-semibold text-foreground">Neo AI</h1>
                <p className="text-xs text-muted-foreground hidden sm:block">Next‑Gen Optimized Advisor, driven by Agentic AI</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <nav className="hidden sm:flex items-center gap-4">
                <Link
                  href="/chat"
                  className="text-sm text-muted-foreground hover:text-foreground transition-colors"
                >
                  Chat
                </Link>
                <Link
                  href="/dashboard"
                  className="text-sm text-muted-foreground hover:text-foreground transition-colors"
                >
                  Dashboard
                </Link>
              </nav>
              <ThemeToggle />
            </div>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <main className="flex-1">
        <section className="relative container mx-auto px-4 sm:px-6 py-12 sm:py-20 overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-br from-primary/5 via-transparent to-primary/10 dark:from-primary/10 dark:via-transparent dark:to-primary/5" />
          <div className="relative max-w-4xl mx-auto text-center space-y-6 sm:space-y-8">
            <div className="inline-flex items-center justify-center w-16 h-16 sm:w-20 sm:h-20 rounded-full bg-gradient-to-br from-primary via-primary/80 to-primary/60 mb-4 shadow-lg shadow-primary/20">
              <Sparkles className="w-8 h-8 sm:w-10 sm:h-10 text-primary-foreground" />
            </div>
            <h1 className="text-3xl sm:text-4xl md:text-5xl lg:text-6xl font-bold leading-tight bg-gradient-to-r from-primary via-primary/90 to-primary/70 bg-clip-text text-transparent">
              Neo AI
            </h1>
            <p className="text-lg sm:text-xl md:text-2xl text-muted-foreground max-w-2xl mx-auto">
              Next‑Gen Optimized Advisor, driven by Agentic AI
            </p>
            <p className="text-sm sm:text-base text-muted-foreground max-w-xl mx-auto">
              Get accurate, source-backed answers from official documents and trusted sources 
              including regulatory bodies, financial institutions, and compliance organizations.
            </p>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-4">
              <Button asChild size="lg" className="w-full sm:w-auto bg-gradient-to-r from-primary via-primary/90 to-primary/80 hover:from-primary/90 hover:via-primary/80 hover:to-primary/70 shadow-lg shadow-primary/20">
                <Link href="/chat">
                  Start Chatting
                  <ArrowRight className="ml-2 w-4 h-4" />
                </Link>
              </Button>
              <Button asChild variant="outline" size="lg" className="w-full sm:w-auto">
                <Link href="/dashboard">
                  <BarChart3 className="mr-2 w-4 h-4" />
                  View Dashboard
                </Link>
              </Button>
            </div>
          </div>
        </section>

        {/* Features Section */}
        <section className="container mx-auto px-4 sm:px-6 py-12 sm:py-20">
          <div className="max-w-6xl mx-auto">
            <div className="text-center mb-12 sm:mb-16">
              <h2 className="text-2xl sm:text-3xl md:text-4xl font-bold text-foreground mb-4">
                Powerful Features
              </h2>
              <p className="text-muted-foreground max-w-2xl mx-auto">
                Access comprehensive Islamic finance knowledge through advanced AI-powered search and retrieval
              </p>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 sm:gap-8">
              {features.map((feature, index) => (
                <div
                  key={index}
                  className="bg-card border border-border rounded-lg p-6 sm:p-8 hover:border-primary/50 transition-all duration-300 hover:shadow-lg hover:shadow-primary/10 relative overflow-hidden group"
                >
                  <div className="absolute inset-0 bg-gradient-to-br from-primary/5 via-transparent to-primary/10 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                  <div className="relative z-10">
                    <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-primary via-primary/80 to-primary/60 flex items-center justify-center mb-4 text-primary-foreground shadow-md shadow-primary/20">
                      {feature.icon}
                    </div>
                    <h3 className="text-lg sm:text-xl font-semibold text-foreground mb-2">
                      {feature.title}
                    </h3>
                    <p className="text-sm sm:text-base text-muted-foreground">
                      {feature.description}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* CTA Section */}
        <section className="container mx-auto px-4 sm:px-6 py-12 sm:py-20">
          <div className="max-w-4xl mx-auto">
            <div className="relative bg-card border border-border rounded-lg p-8 sm:p-12 text-center overflow-hidden">
              <div className="absolute inset-0 bg-gradient-to-br from-primary/10 via-primary/5 to-transparent opacity-50" />
              <div className="relative z-10">
                <h2 className="text-2xl sm:text-3xl font-bold bg-gradient-to-r from-primary via-primary/90 to-primary/70 bg-clip-text text-transparent mb-4">
                  Ready to get started?
                </h2>
                <p className="text-muted-foreground mb-6 sm:mb-8 max-w-2xl mx-auto">
                  Start asking questions about Islamic finance and Shariah compliance. 
                  Get instant, accurate answers backed by official documents from trusted sources.
                </p>
                <Button asChild size="lg" className="bg-gradient-to-r from-primary via-primary/90 to-primary/80 hover:from-primary/90 hover:via-primary/80 hover:to-primary/70 shadow-lg shadow-primary/20">
                  <Link href="/chat">
                    Start Chatting Now
                    <ArrowRight className="ml-2 w-4 h-4" />
                  </Link>
                </Button>
              </div>
            </div>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="border-t border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container mx-auto px-4 sm:px-6 py-6">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-primary" />
              <p className="text-sm text-muted-foreground">Neo AI - Next‑Gen Optimized Advisor, driven by Agentic AI</p>
            </div>
            <nav className="flex items-center gap-4">
              <Link
                href="/chat"
                className="text-sm text-muted-foreground hover:text-foreground transition-colors"
              >
                Chat
              </Link>
              <Link
                href="/dashboard"
                className="text-sm text-muted-foreground hover:text-foreground transition-colors"
              >
                Dashboard
              </Link>
            </nav>
          </div>
        </div>
      </footer>
    </div>
  );
}
