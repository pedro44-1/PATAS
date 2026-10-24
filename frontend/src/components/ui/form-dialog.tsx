import type { ReactNode } from "react";

import { cn } from "@/lib/utils";
import { Dialog, DialogContent, DialogDescription, DialogTitle } from "@/components/ui/dialog";

const SIZES = {
  md: "sm:max-w-md",
  lg: "sm:max-w-lg",
  xl: "sm:max-w-2xl",
  "2xl": "sm:max-w-4xl",
} as const;

interface FormDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: ReactNode;
  description?: ReactNode;
  size?: keyof typeof SIZES;
  children: ReactNode;
  className?: string;
}

export function FormDialog({ open, onOpenChange, title, description, size = "md", children, className }: FormDialogProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent
        className={cn(
          "flex max-h-[calc(100dvh-2rem)] w-full flex-col gap-0 overflow-hidden rounded-2xl p-0",
          SIZES[size],
          className,
        )}
      >
        <div className="border-b border-border/70 px-6 py-4 pr-12">
          <DialogTitle className="font-bold text-foreground">{title}</DialogTitle>
          {description && <DialogDescription className="mt-1 text-xs">{description}</DialogDescription>}
        </div>
        <div className="min-h-0 flex-1 overflow-y-auto">{children}</div>
      </DialogContent>
    </Dialog>
  );
}
