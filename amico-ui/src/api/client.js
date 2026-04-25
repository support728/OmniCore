import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("amico-auth-token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
    console.log("TOKEN ATTACHED:", token);
  } else {
    window.location.href = "/login";
    return Promise.reject("No token");
  }
  return config;
});

export default api;
