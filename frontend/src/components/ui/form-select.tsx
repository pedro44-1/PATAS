import type { ReactNode } from "react";

import { cn } from "@/lib/utils";
import { ComboboxSelect } from "@/components/ui/combobox-select";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

export interface FormSelectOption {
  value: string | number;
  label: ReactNode;
  disabled?: boolean;
  variant?: "default" | "action";
}

interface FormSelectProps {
  value: string | number | null | undefined;
  onValueChange: (value: string) => void;
  options: FormSelectOption[];
  placeholder?: string;
  disabled?: boolean;
  required?: boolean;
  id?: string;
  name?: string;
  className?: string;
  ariaLabel?: string;
  searchable?: boolean;
  onSearchChange?: (query: string) => void;
}

const SEARCHABLE_THRESHOLD = 10;

export function FormSelect({
  value,
  onValueChange,
  options,
  placeholder,
  disabled,
  required,
  id,
  name,
  className,
  ariaLabel,
  searchable,
  onSearchChange,
}: FormSelectProps) {
  const normalizedOptions = options.map((option) => ({
    ...option,
    value: String(option.value),
  }));
  const normalizedValue = value === null || value === undefined ? null : String(value);
  const textOptions = normalizedOptions.every((option) => typeof option.label === "string");
  const useSearch = textOptions && (searchable ?? (Boolean(onSearchChange) || normalizedOptions.length > SEARCHABLE_THRESHOLD));

  if (useSearch) {
    return (
      <ComboboxSelect
        value={normalizedValue}
        onValueChange={onValueChange}
        items={normalizedOptions.map((option) => ({ ...option, label: option.label as string }))}
        placeholder={placeholder}
        disabled={disabled}
        required={required}
        id={id}
        name={name}
        className={className}
        ariaLabel={ariaLabel}
        onSearchChange={onSearchChange}
      />
    );
  }

  return (
    <Select
      value={normalizedValue}
      onValueChange={(nextValue) => {
        if (nextValue !== null) onValueChange(nextValue);
      }}
      items={normalizedOptions}
      disabled={disabled}
      required={required}
      id={id}
      name={name}
    >
      <SelectTrigger
        aria-label={ariaLabel}
        className={cn("h-10 w-full rounded-xl bg-background px-3", className)}
      >
        <SelectValue placeholder={placeholder} />
      </SelectTrigger>
      <SelectContent
        align="start"
        alignItemWithTrigger={false}
        className="min-w-[var(--anchor-width)]"
      >
        {normalizedOptions.map((option) => (
          <SelectItem
            key={option.value}
            value={option.value}
            disabled={option.disabled}
            className={cn(
              "px-3 py-2",
              option.variant === "action" &&
                "mb-1 border-b border-border pb-2.5 font-semibold text-brand-700 focus:text-brand-700",
            )}
          >
            {option.label}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}
