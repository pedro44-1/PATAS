import { PawPrint } from "lucide-react";
import { useTranslation } from "react-i18next";
import { cn } from "@/lib/utils";

export function BrandMark({ compact = false, className }: { compact?: boolean; className?: string }) {
  const { t } = useTranslation();

  return (
    <div className={cn("flex items-center gap-3", className)}>
      <span className="flex size-10 items-center justify-center rounded-2xl bg-primary text-primary-foreground shadow-[0_10px_24px_oklch(var(--primary)/0.25)]">
        <PawPrint className="size-5" strokeWidth={2.4} />
      </span>
      {!compact && (
        <span className="leading-none">
          <span className="block text-lg font-bold tracking-[0.18em] text-foreground">{t("app.name")}</span>
          <span className="mt-1 block text-[0.62rem] font-semibold uppercase tracking-[0.16em] text-muted-foreground">{t("app.tagline")}</span>
        </span>
      )}
    </div>
  );
}
