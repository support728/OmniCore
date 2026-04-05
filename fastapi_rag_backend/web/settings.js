const
default_backend_base_url ="http://127.0.0.1:8000";async function apiFetch(url,  options = {}) { return fetch(default_backend_base_url + url, options); }
window.apiFetch = apiFetch;
  

