import { useCallback, useEffect, useRef, useState } from "react";

import { useDebouncedValue } from "@/lib/use-debounced-value";

export function mergeById<T extends { id: number }>(base: T[], extra: T[]): T[] {
  const known = new Set(base.map((item) => item.id));
  return [...base, ...extra.filter((item) => !known.has(item.id))];
}

export function useRemoteOptions<T extends { id: number }>(search: (query: string) => Promise<T[]>) {
  const [found, setFound] = useState<T[]>([]);
  const [query, setQuery] = useState("");
  const debounced = useDebouncedValue(query.trim());
  const searchRef = useRef(search);
  searchRef.current = search;

  useEffect(() => {
    if (debounced.length < 2) return;
    let active = true;
    searchRef.current(debounced)
      .then((items) => {
        if (active) setFound((current) => mergeById(current, items));
      })
      .catch(() => undefined);
    return () => {
      active = false;
    };
  }, [debounced]);

  const withFound = useCallback((base: T[]) => mergeById(base, found), [found]);

  return { onSearchChange: setQuery, withFound };
}
