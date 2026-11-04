import { useCallback, useEffect, useRef, useState } from "react";
import { NoDataError } from "./client";

export interface QueryState<T> {
  data: T | null;
  loading: boolean;
  error: Error | null;
  empty: boolean;
  refresh: () => void;
}

export function usePolling<T>(
  fetcher: () => Promise<T>,
  intervalMs: number | null,
  deps: unknown[] = [],
): QueryState<T> {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<Error | null>(null);
  const [loading, setLoading] = useState(true);
  const [empty, setEmpty] = useState(false);
  const [tick, setTick] = useState(0);
  const fetcherRef = useRef(fetcher);
  fetcherRef.current = fetcher;

  const refresh = useCallback(() => setTick((t) => t + 1), []);

  useEffect(() => {
    let cancelled = false;
    let timer: number | undefined;

    const run = async () => {
      try {
        const result = await fetcherRef.current();
        if (cancelled) return;
        setData(result);
        setEmpty(Array.isArray(result) && result.length === 0);
        setError(null);
      } catch (e) {
        if (cancelled) return;
        if (e instanceof NoDataError) {
          setEmpty(true);
          setError(null);
        } else {
          setError(e instanceof Error ? e : new Error(String(e)));
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
      if (!cancelled && intervalMs !== null) {
        timer = window.setTimeout(run, document.hidden ? Math.max(intervalMs, 10_000) : intervalMs);
      }
    };

    setLoading(true);
    void run();

    const onVisible = () => {
      if (!document.hidden && intervalMs !== null) {
        window.clearTimeout(timer);
        void run();
      }
    };
    document.addEventListener("visibilitychange", onVisible);

    return () => {
      cancelled = true;
      window.clearTimeout(timer);
      document.removeEventListener("visibilitychange", onVisible);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [intervalMs, tick, ...deps]);

  return { data, loading, error, empty, refresh };
}
