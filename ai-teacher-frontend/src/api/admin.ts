import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api/v1';

// Admin API
export const adminApi = {
  // Login
  login: async (phone: string, password: string) => {
    const response = await axios.post(`${API_BASE_URL}/admin/login`, { phone, password });
    return response.data;
  },

  // Get profile
  getProfile: async (token: string) => {
    const response = await axios.get(`${API_BASE_URL}/admin/profile`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    return response.data;
  },

  // Get dashboard
  getDashboard: async (token: string) => {
    const response = await axios.get(`${API_BASE_URL}/admin/dashboard`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    return response.data;
  },
};

// Chapter API
export const chapterApi = {
  // List chapters
  list: async (token: string, params?: { grade?: string; edition?: string; subject?: string }) => {
    const response = await axios.get(`${API_BASE_URL}/admin/chapters`, {
      headers: { Authorization: `Bearer ${token}` },
      params,
    });
    return response.data;
  },

  // Create chapter
  create: async (token: string, data: any) => {
    const response = await axios.post(`${API_BASE_URL}/admin/chapters`, data, {
      headers: { Authorization: `Bearer ${token}` },
    });
    return response.data;
  },

  // Get chapter
  get: async (token: string, chapterId: string) => {
    const response = await axios.get(`${API_BASE_URL}/admin/chapters/${chapterId}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    return response.data;
  },

  // Update chapter
  update: async (token: string, chapterId: string, data: any) => {
    const response = await axios.put(`${API_BASE_URL}/admin/chapters/${chapterId}`, data, {
      headers: { Authorization: `Bearer ${token}` },
    });
    return response.data;
  },

  // Delete chapter
  delete: async (token: string, chapterId: string) => {
    const response = await axios.delete(`${API_BASE_URL}/admin/chapters/${chapterId}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    return response.data;
  },
};

// Knowledge Point API
export const knowledgePointApi = {
  // List knowledge points
  list: async (token: string, chapterId: string, params?: { level?: number; type?: string }) => {
    const response = await axios.get(`${API_BASE_URL}/admin/chapters/${chapterId}/knowledge-points`, {
      headers: { Authorization: `Bearer ${token}` },
      params,
    });
    return response.data;
  },

  // Create knowledge point
  create: async (token: string, chapterId: string, data: any) => {
    const response = await axios.post(`${API_BASE_URL}/admin/chapters/${chapterId}/knowledge-points`, data, {
      headers: { Authorization: `Bearer ${token}` },
    });
    return response.data;
  },

  // Get knowledge point
  get: async (token: string, kpId: string) => {
    const response = await axios.get(`${API_BASE_URL}/admin/knowledge-points/${kpId}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    return response.data;
  },

  // Update knowledge point
  update: async (token: string, kpId: string, data: any) => {
    const response = await axios.put(`${API_BASE_URL}/admin/knowledge-points/${kpId}`, data, {
      headers: { Authorization: `Bearer ${token}` },
    });
    return response.data;
  },

  // Delete knowledge point
  delete: async (token: string, kpId: string) => {
    const response = await axios.delete(`${API_BASE_URL}/admin/knowledge-points/${kpId}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    return response.data;
  },

  // Add dependency
  addDependency: async (token: string, kpId: string, dependsOnKpId: string) => {
    const response = await axios.post(
      `${API_BASE_URL}/admin/knowledge-points/${kpId}/dependencies`,
      { depends_on_kp_id: dependsOnKpId },
      { headers: { Authorization: `Bearer ${token}` } }
    );
    return response.data;
  },

  // Remove dependency
  removeDependency: async (token: string, kpId: string, depId: number) => {
    const response = await axios.delete(
      `${API_BASE_URL}/admin/knowledge-points/${kpId}/dependencies/${depId}`,
      { headers: { Authorization: `Bearer ${token}` } }
    );
    return response.data;
  },
};
