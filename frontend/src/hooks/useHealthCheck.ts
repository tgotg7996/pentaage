import { useEffect, useState } from "react";
import { client } from "../api/client";

interface HealthStatus {
  status: string;
  components: Record<string, string>;
}

export function useHealthCheck(intervalMs = 30000) {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    let stopped = false;

    const check = async () => {
      try {
        const res = await fetch(`${client.baseURL}/health`);
        if (!res.ok) throw new Error();
        const data = (await res.json()) as HealthStatus;
        if (!stopped) {
          setHealth(data);
          setError(false);
        }
      } catch {
        if (!stopped) {
          setHealth(null);
          setError(true);
        }
      }
    };

    void check();
    const timer = setInterval(() => void check(), intervalMs);

    return () => {
      stopped = true;
      clearInterval(timer);
    };
  }, [intervalMs]);

  return { health, error };
}
