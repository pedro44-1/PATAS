import type { ReactNode } from "react";

import { cn } from "@/lib/utils";
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
}

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
}: FormSelectProps) {
  const normalizedOptions = options.map((option) => ({
    ...option,
    value: String(option.value),
  }));
  const normalizedValue = value === null || value === undefined ? null : String(value);

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
                "mt-1 border-t border-border pt-2.5 font-semibold text-brand-700 focus:text-brand-700",
            )}
          >
            {option.label}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}
