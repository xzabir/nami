const API_BASE = '/api';

export function getToken() {
  return localStorage.getItem('nami_token');
}

export function setToken(token) {
  localStorage.setItem('nami_token', token);
}

export function clearToken() {
  localStorage.removeItem('nami_token');
}

export async function apiRequest(path, { method = 'GET', body = null, auth = true } = {}) {
  const headers = {};
  if (!(body instanceof FormData)) {
    headers['Content-Type'] = 'application/json';
  }
  if (auth) {
    const token = getToken();
    if (token) headers['Authorization'] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE}${path}`, {
    method,
    headers,
    body: body instanceof FormData ? body : (body ? JSON.stringify(body) : undefined),
  });

  let data = null;
  try {
    data = await res.json();
  } catch (_) {
    // no body
  }

  if (!res.ok) {
    const message = (data && data.detail) || `Request failed (${res.status})`;
    throw new Error(message);
  }

  return data;
}
