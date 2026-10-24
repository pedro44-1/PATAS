import { useMemo, useState } from "react";
import { Combobox } from "@base-ui/react/combobox";
import { CheckIcon, ChevronDownIcon } from "lucide-react";
import { useTranslation } from "react-i18next";

import { cn } from "@/lib/utils";

export interface ComboboxSelectItem {
  value: string;
  label: string;
  disabled?: boolean;
  variant?: "default" | "action";
}

interface ComboboxSelectProps {
  value: string | null;
  onValueChange: (value: string) => void;
  items: ComboboxSelectItem[];
  placeholder?: string;
  disabled?: boolean;
  required?: boolean;
  id?: string;
  name?: string;
  className?: string;
  ariaLabel?: string;
  onSearchChange?: (query: string) => void;
}

const normalize = (text: string) => text.normalize("NFD").replace(/\p{Diacritic}/gu, "").toLowerCase();

export function ComboboxSelect({
  value,
  onValueChange,
  items,
  placeholder,
  disabled,
  required,
  id,
  name,
  className,
  ariaLabel,
  onSearchChange,
}: ComboboxSelectProps) {
  const { t } = useTranslation();
  const [query, setQuery] = useState("");
  const selected = items.find((item) => item.value === value) ?? null;
  const orderedItems = useMemo(() => {
    if (!query.trim()) return items;
    return [...items.filter((item) => item.variant !== "action"), ...items.filter((item) => item.variant === "action")];
  }, [items, query]);

  return (
    <Combobox.Root<ComboboxSelectItem>
      items={orderedItems}
      value={selected}
      onValueChange={(item) => {
        if (item) onValueChange(item.value);
      }}
      isItemEqualToValue={(item, current) => item.value === current.value}
      filter={(item, query) => item.variant === "action" || normalize(item.label).includes(normalize(query))}
      onInputValueChange={(nextQuery, details) => {
        if (details.reason !== "input-change" && details.reason !== "input-clear") return;
        setQuery(nextQuery);
        onSearchChange?.(nextQuery);
      }}
      autoHighlight
      disabled={disabled}
      required={required}
      name={name}
    >
      <Combobox.InputGroup className={cn("relative h-10 w-full", className)}>
        <Combobox.Input
          id={id}
          aria-label={ariaLabel}
          placeholder={placeholder}
          className="h-full w-full rounded-xl border border-input bg-background pr-9 pl-3 text-sm outline-none placeholder:text-muted-foreground focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50 disabled:cursor-not-allowed disabled:opacity-50 dark:bg-input/30"
        />
        <Combobox.Trigger
          aria-label={t("common.openOptions")}
          className="absolute inset-y-0 right-0 flex w-9 items-center justify-center text-muted-foreground"
        >
          <ChevronDownIcon className="size-4" />
        </Combobox.Trigger>
      </Combobox.InputGroup>
      <Combobox.Portal>
        <Combobox.Positioner className="isolate z-[100] outline-none" sideOffset={4}>
          <Combobox.Popup className="w-[var(--anchor-width)] max-w-[var(--available-width)] overflow-hidden rounded-lg bg-popover text-popover-foreground shadow-md ring-1 ring-foreground/10">
            <Combobox.Empty>
              <div className="px-3 py-3 text-sm text-muted-foreground">{t("common.noResults")}</div>
            </Combobox.Empty>
            <Combobox.List className="max-h-[min(20rem,var(--available-height))] overflow-y-auto overscroll-contain p-1 outline-0 data-empty:p-0">
              {(item: ComboboxSelectItem) => (
                <Combobox.Item
                  key={item.value}
                  value={item}
                  disabled={item.disabled}
                  className={cn(
                    "flex cursor-default items-center gap-2 rounded-md px-3 py-2 text-sm outline-none select-none data-disabled:opacity-50 data-highlighted:bg-accent data-highlighted:text-accent-foreground",
                    item.variant === "action" && "mb-1 border-b border-border pb-2.5 font-semibold text-brand-700",
                  )}
                >
                  <span className="flex-1">{item.label}</span>
                  <Combobox.ItemIndicator>
                    <CheckIcon className="size-4" />
                  </Combobox.ItemIndicator>
                </Combobox.Item>
              )}
            </Combobox.List>
          </Combobox.Popup>
        </Combobox.Positioner>
      </Combobox.Portal>
    </Combobox.Root>
  );
}
