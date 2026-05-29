import axios from 'axios';

let getToken = () => null;

/**
 * Used by AuthContext to inject the memory-only token into the API client
 */
export const setTokenGetter = (fn) => {
    getToken = fn;
};

const baseConfig = {
    baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
    timeout: 10000,
    withCredentials: true // Always send cookies (for refresh token)
};

export const apiClient = axios.create(baseConfig);
export const mlClient = axios.create({ ...baseConfig, timeout: 90000 }); // 90s for ML endpoints

const authInterceptor = (config) => {
    const token = getToken();
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
};

apiClient.interceptors.request.use(authInterceptor);
mlClient.interceptors.request.use(authInterceptor);

const responseInterceptor = async (error) => {
    if (error.response) {
        if (error.response.status === 401 && !error.config._retry) {
            error.config._retry = true;
            try {
                // Let AuthContext handle the actual refresh flow, 
                // but this allows a seamless retry if the context already refreshed it in parallel
                const token = getToken();
                if(token) {
                   error.config.headers.Authorization = `Bearer ${token}`;
                   return apiClient(error.config);
                }
            } catch (e) {
                return Promise.reject(error);
            }
        }
        if (error.response.status === 429) {
            const retryAfter = error.response.headers['retry-after'] || 60;
            const event = new CustomEvent('rate-limit-exceeded', { detail: { retryAfter } });
            window.dispatchEvent(event);
        }
        if (error.response.status === 503 && !error.config._retry) {
            // ML Circuit breaker or Model loading
            console.warn("Service 503: Model likely loading or circuit open.");
        }
    } else {
        console.error("Unable to connect to server");
    }
    return Promise.reject(error);
};

apiClient.interceptors.response.use((res) => res, responseInterceptor);
mlClient.interceptors.response.use((res) => res, responseInterceptor);
