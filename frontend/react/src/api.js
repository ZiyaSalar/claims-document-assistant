const BASE = import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, '') || '';

export async function api(path, { method = 'GET', body, form } = {}) {
    const options = { method, headers: { Accept: 'application/json' } };

    if (form) {
        options.body = form;
    } else if (body !== undefined) {
        options.headers['Content-Type'] = 'application/json';
        options.body = JSON.stringify(body);
    }

    let response;
    try {
        response = await fetch(`${BASE}${path}`, options);
    } catch {
        throw new Error(
            'Cannot connect to FastAPI. Check port 8000 and Vite proxy.'
        );
    }

    const raw = await response.text();
    let data;
    try {
        data = raw ? JSON.parse(raw) : null;
    } catch {
        throw new Error(
            `Unexpected response from API (HTTP ${response.status}).`
        );
    }

    if (!response.ok) {
        const detail =
            typeof data?.detail === 'string'
                ? data.detail
                : JSON.stringify(data?.detail || data || 'Request failed');
        throw new Error(`HTTP ${response.status}: ${detail}`);
    }

    return data;
}
