import { useEffect, useId, useState } from "react";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

interface PromptDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: string;
  description?: string;
  label: string;
  confirmLabel: string;
  cancelLabel: string;
  onConfirm: (value: string) => void;
  initialValue?: string;
  pending?: boolean;
  destructive?: boolean;
  maxLength?: number;
}

export function PromptDialog({
  open,
  onOpenChange,
  title,
  description,
  label,
  confirmLabel,
  cancelLabel,
  onConfirm,
  initialValue = "",
  pending = false,
  destructive = false,
  maxLength = 255,
}: PromptDialogProps) {
  const inputId = useId();
  const [value, setValue] = useState(initialValue);

  useEffect(() => {
    if (open) setValue(initialValue);
  }, [open, initialValue]);

  return (
    <Dialog open={open} onOpenChange={(next) => !pending && onOpenChange(next)}>
      <DialogContent showCloseButton={false}>
        <form
          className="grid gap-4"
          onSubmit={(event) => {
            event.preventDefault();
            if (value.trim()) onConfirm(value.trim());
          }}
        >
          <DialogHeader>
            <DialogTitle>{title}</DialogTitle>
            {description && <DialogDescription>{description}</DialogDescription>}
          </DialogHeader>
          <div className="grid gap-1.5">
            <Label htmlFor={inputId}>{label}</Label>
            <Input id={inputId} value={value} maxLength={maxLength} required autoFocus onChange={(event) => setValue(event.target.value)} />
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" disabled={pending} onClick={() => onOpenChange(false)}>
              {cancelLabel}
            </Button>
            <Button type="submit" variant={destructive ? "destructive" : "default"} disabled={pending || !value.trim()}>
              {confirmLabel}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
