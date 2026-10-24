import { ChevronLeft, ChevronRight } from "lucide-react";
import { Button } from "@/components/ui/button";

interface PaginationProps {
  page: number;
  pageSize: number;
  total: number;
  onPageChange: (page: number) => void;
  label: (range: { from: number; to: number; total: number }) => string;
  previousLabel: string;
  nextLabel: string;
}

export function Pagination({ page, pageSize, total, onPageChange, label, previousLabel, nextLabel }: PaginationProps) {
  if (total <= pageSize) return null;
  const lastPage = Math.max(0, Math.ceil(total / pageSize) - 1);
  const from = page * pageSize + 1;
  const to = Math.min(total, (page + 1) * pageSize);
  return (
    <nav className="flex items-center justify-between gap-3 px-4 py-3 text-sm text-muted-foreground" aria-label={label({ from, to, total })}>
      <span>{label({ from, to, total })}</span>
      <div className="flex gap-2">
        <Button type="button" variant="outline" size="sm" disabled={page === 0} onClick={() => onPageChange(page - 1)} aria-label={previousLabel}>
          <ChevronLeft className="size-4" />
        </Button>
        <Button type="button" variant="outline" size="sm" disabled={page >= lastPage} onClick={() => onPageChange(page + 1)} aria-label={nextLabel}>
          <ChevronRight className="size-4" />
        </Button>
      </div>
    </nav>
  );
}
