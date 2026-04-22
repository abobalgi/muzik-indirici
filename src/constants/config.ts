export const API_SERVERS = [
  'http://217.154.94.16:11463',
  'http://212.132.99.151:11535',
];

export const CF_WORKER = 'https://flux-proxy.schatzei1007.workers.dev';

/** Randomly picks a server, falls back to the other on failure */
export async function fetchSmart(endpoint: string, options?: RequestInit): Promise<Response> {
  const servers = [...API_SERVERS].sort(() => Math.random() - 0.5);
  let lastError: Error | null = null;

  for (const server of servers) {
    try {
      const res = await fetch(`${server}${endpoint}`, {
        ...options,
        headers: { 'Accept': 'application/json', ...(options?.headers ?? {}) },
      });
      if (res.ok) return res;
    } catch (e) {
      lastError = e as Error;
    }
  }
  throw lastError ?? new Error('Tüm sunucular yanıt vermedi');
}

/** Returns streaming URL for a given video ID */
export function streamUrl(videoId: string, serverIndex = 0): string {
  return `${API_SERVERS[serverIndex % API_SERVERS.length]}/stream_audio?id=${videoId}`;
}

/** Returns download URL for a given video ID */
export function downloadUrl(videoId: string, serverIndex = 0): string {
  return `${API_SERVERS[serverIndex % API_SERVERS.length]}/download?id=${videoId}`;
}
