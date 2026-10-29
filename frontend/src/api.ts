export type Category = { id: number; name: string; slug: string; description: string };
export type Location = { id: number; name: string; city: string; country_code: string; latitude: string | null; longitude: string | null };
export type Photo = { id: number; object_key: string; alt_text: string; position: number; is_primary: boolean };
export type Equipment = {
  id: number; name: string; slug: string; description: string; company_name: string; location: Location;
  categories: Category[]; photos: Photo[]; base_rate: string; billing_unit: 'hour' | 'day';
  minimum_rental_hours: number; deposit_amount: string; currency: string; status: string;
};
export type Paginated<T> = { count: number; next: string | null; previous: string | null; results: T[] };

function readCookie(name: string): string | null {
  const row = document.cookie.split('; ').find((part) => part.startsWith(`${name}=`));
  return row ? decodeURIComponent(row.slice(name.length + 1)) : null;
}

export async function api<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  if (init.body && !headers.has('Content-Type')) headers.set('Content-Type', 'application/json');
  const method = (init.method ?? 'GET').toUpperCase();
  if (!['GET', 'HEAD', 'OPTIONS', 'TRACE'].includes(method)) {
    const csrf = readCookie('csrftoken');
    if (csrf) headers.set('X-CSRFToken', csrf);
  }
  const response = await fetch(path, { ...init, headers, credentials: 'same-origin' });
  if (response.status === 204) return undefined as T;
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = typeof data.detail === 'string' ? data.detail : Object.values(data).flat().join(' ');
    throw new Error(detail || `Request failed (${response.status})`);
  }
  return data as T;
}

export async function ensureCsrf(): Promise<void> {
  await api<{ csrfToken: string }>('/api/auth/csrf/');
}
