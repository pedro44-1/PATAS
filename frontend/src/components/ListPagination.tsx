import { useTranslation } from "react-i18next";
import { Pagination } from "@/components/ui/pagination";
import { PAGE_SIZE } from "@/api/pagination";

interface ListPaginationProps {
  page: number;
  total: number;
  onPageChange: (page: number) => void;
  pageSize?: number;
}

export function ListPagination({ page, total, onPageChange, pageSize = PAGE_SIZE }: ListPaginationProps) {
  const { t } = useTranslation();
  return (
    <Pagination
      page={page}
      pageSize={pageSize}
      total={total}
      onPageChange={onPageChange}
      label={(range) => t("pagination.range", range)}
      previousLabel={t("pagination.previous")}
      nextLabel={t("pagination.next")}
    />
  );
}
