import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { Compass } from "lucide-react";

import { buttonVariants } from "@/components/ui/button";

export default function NotFound() {
  const { t } = useTranslation();
  return (
    <div className="flex flex-col items-center justify-center gap-4 py-24 text-center">
      <Compass className="size-10 text-muted-foreground" aria-hidden="true" />
      <div>
        <h2 className="text-xl font-bold text-foreground">{t("notFound.title")}</h2>
        <p className="mt-1 text-sm text-muted-foreground">{t("notFound.description")}</p>
      </div>
      <Link to="/dashboard" className={buttonVariants()}>{t("notFound.back")}</Link>
    </div>
  );
}
