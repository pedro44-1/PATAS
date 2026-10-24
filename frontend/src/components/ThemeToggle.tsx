import { useEffect, useState } from "react";
import { Moon, Sun } from "lucide-react";
import { useTranslation } from "react-i18next";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

function storedTheme() {
  return localStorage.getItem("patas_theme") === "dark" ? "dark" : "light";
}

export function ThemeToggle({ className }: { className?: string }) {
  const [theme, setTheme] = useState<"light" | "dark">(storedTheme);
  const { t } = useTranslation();
  const isDark = theme === "dark";

  useEffect(() => {
    document.documentElement.classList.toggle("dark", isDark);
    localStorage.setItem("patas_theme", theme);
  }, [isDark, theme]);

  return (
    <Button
      type="button"
      variant="ghost"
      size="icon"
      className={cn("rounded-xl text-muted-foreground hover:bg-muted hover:text-foreground", className)}
      onClick={() => setTheme(isDark ? "light" : "dark")}
      title={isDark ? t("common.useLightTheme") : t("common.useDarkTheme")}
      aria-label={isDark ? t("common.useLightTheme") : t("common.useDarkTheme")}
    >
      {isDark ? <Sun className="size-4" /> : <Moon className="size-4" />}
    </Button>
  );
}
