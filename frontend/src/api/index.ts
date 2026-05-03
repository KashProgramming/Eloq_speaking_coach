import { apiClient } from './client';

export const api = {
  auth: {
    login: (data: any) => apiClient.post('/auth/login', data).then(res => res.data),
    signup: (data: any) => apiClient.post('/auth/signup', data).then(res => res.data),
    refresh: (refreshToken: string) => apiClient.post('/auth/refresh', { refresh_token: refreshToken }).then(res => res.data),
    deleteAccount: () => apiClient.delete('/auth/account').then(res => res.data),
    changePassword: (data: { current_password: string; new_password: string }) => apiClient.put('/auth/password', data).then(res => res.data),
  },
  practice: {
    getPrompt: () => apiClient.get('/practice/prompt').then(res => res.data),
    analyze: (formData: FormData) => apiClient.post('/practice/analyze', formData).then(res => res.data),
    retry: (formData: FormData) => apiClient.post('/practice/retry', formData).then(res => res.data),
    getProgress: (period: 'week' | 'month' | 'all' = 'week') => apiClient.get('/practice/progress', { params: { period } }).then(res => res.data),
    getIdealAnswer: (sessionId: string) => apiClient.get(`/practice/session/${sessionId}/ideal-answer`).then(res => res.data),
    getHistory: (limit = 50, offset = 0) => apiClient.get('/practice/history', { params: { limit, offset } }).then(res => res.data),
    getGroupedHistory: (limit = 50, offset = 0) => apiClient.get('/practice/history/grouped', { params: { limit, offset } }).then(res => res.data),
    getSessionDetail: (sessionId: string) => apiClient.get(`/practice/session/${sessionId}`).then(res => res.data),
  },
  roleplay: {
    start: (data: any) => apiClient.post('/roleplay/start', data).then(res => res.data),
    respond: (formData: FormData) => apiClient.post('/roleplay/respond', formData).then(res => res.data),
    history: (sessionId: string) => apiClient.get(`/roleplay/${sessionId}/history`).then(res => res.data),
    getSessions: (limit = 50, offset = 0) => apiClient.get('/roleplay/sessions/list', { params: { limit, offset } }).then(res => res.data),
    getSessionDetail: (sessionId: string) => apiClient.get(`/roleplay/sessions/${sessionId}`).then(res => res.data),
  }
};
