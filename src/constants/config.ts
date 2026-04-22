export const CF_WORKER = 'https://flux-proxy.schatzei1007.workers.dev';

/** Bütün API istekleri doğrudan güvenli Cloudflare Worker üzerinden geçer */
export async function fetchSmart(endpoint: string, options?: RequestInit): Promise<Response> {
  try {
    const res = await fetch(`${CF_WORKER}${endpoint}`, {
      ...options,
      headers: { 'Accept': 'application/json', ...(options?.headers ?? {}) },
    });
    
    if (res.ok) return res;
    throw new Error(`HTTP Hatası: ${res.status}`);
  } catch (e) {
    throw new Error('Sunucuya ulaşılamadı veya bağlantı reddedildi.');
  }
}

/** Müzik dinleme (stream) bağlantısını Cloudflare üzerinden döndürür */
export function streamUrl(videoId: string): string {
  return `${CF_WORKER}/stream_audio?id=${videoId}`;
}

/** İndirme (download) bağlantısını Cloudflare üzerinden döndürür */
export function downloadUrl(videoId: string): string {
  return `${CF_WORKER}/download?id=${videoId}`;
}
