'use client';

import { Button } from '@/components/ui/button';
import { Menu } from 'lucide-react';

interface SidebarToggleProps {
  onToggle: () => void;
}

export function SidebarToggle({ onToggle }: SidebarToggleProps) {
  return (
    <Button
      variant="ghost"
      size="icon"
      onClick={onToggle}
      className="md:hidden"
    >
      <Menu className="h-5 w-5" />
    </Button>
  );
}
