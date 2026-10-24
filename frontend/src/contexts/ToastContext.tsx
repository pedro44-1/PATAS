import { createContext, useCallback, useContext, useMemo, useRef, useState, type ReactNode } from "react";
import { CheckCircle2, X, XCircle } from "lucide-react";
import { useTranslation } from "react-i18next";

import { cn } from "@/lib/utils";

type ToastTone = "success" | "error";

interface ToastItem {
  id: number;
  tone: ToastTone;
  message: string;
}

interface ToastApi {
  success: (message: string) => void;
  error: (message: string) => void;
}

const TOAST_DURATION_MS = 4500;
const noop = () => undefined;
const ToastContext = createContext<ToastApi>({ success: noop, error: noop });

export function ToastProvider({ children }: { children: ReactNode }) {
  const { t } = useTranslation();
  const [toasts, setToasts] = useState<ToastItem[]>([]);
  const nextId = useRef(0);

  const dismiss = useCallback((id: number) => {
    setToasts((current) => current.filter((toast) => toast.id !== id));
  }, []);

  const push = useCallback((tone: ToastTone, message: string) => {
    const id = ++nextId.current;
    setToasts((current) => [...current.slice(-2), { id, tone, message }]);
    window.setTimeout(() => dismiss(id), TOAST_DURATION_MS);
  }, [dismiss]);

  const api = useMemo<ToastApi>(() => ({
    success: (message) => push("success", message),
    error: (message) => push("error", message),
  }), [push]);

  return (
    <ToastContext.Provider value={api}>
      {children}
      <div aria-live="polite" className="pointer-events-none fixed inset-x-4 bottom-20 z-[120] flex flex-col items-end gap-2 md:bottom-6">
        {toasts.map((toast) => (
          <div
            key={toast.id}
            role={toast.tone === "error" ? "alert" : "status"}
            className={cn(
              "pointer-events-auto flex w-full max-w-sm items-start gap-2 rounded-xl border bg-popover px-4 py-3 text-sm text-popover-foreground shadow-lg",
              toast.tone === "error" ? "border-destructive/30" : "border-emerald-500/30",
            )}
          >
            {toast.tone === "error"
              ? <XCircle className="mt-0.5 size-4 shrink-0 text-destructive" aria-hidden="true" />
              : <CheckCircle2 className="mt-0.5 size-4 shrink-0 text-emerald-600" aria-hidden="true" />}
            <span className="flex-1">{toast.message}</span>
            <button type="button" onClick={() => dismiss(toast.id)} aria-label={t("common.close")} className="text-muted-foreground hover:text-foreground">
              <X className="size-4" />
            </button>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast(): ToastApi {
  return useContext(ToastContext);
}
