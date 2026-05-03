import axios from 'axios';

const API_BASE_URL = 'http://localhost:8008/api/v1';

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

// Grade API
export const gradeApi = {
  // List grades
  list: async (params?: { level?: string; active_only?: boolean }) => {
    const response = await axios.get(`${API_BASE_URL}/admin/grades`, { params });
    return response.data;
  },

  // Create grade
  create: async (data: { name: string; code: string; level: string; sort_order?: number; description?: string }) => {
    const response = await axios.post(`${API_BASE_URL}/admin/grades`, data);
    return response.data;
  },

  // Get grade
  get: async (gradeId: string) => {
    const response = await axios.get(`${API_BASE_URL}/admin/grades/${gradeId}`);
    return response.data;
  },

  // Update grade
  update: async (gradeId: string, data: { name?: string; level?: string; sort_order?: number; description?: string; status?: string }) => {
    const response = await axios.put(`${API_BASE_URL}/admin/grades/${gradeId}`, data);
    return response.data;
  },

  // Delete grade
  delete: async (gradeId: string) => {
    const response = await axios.delete(`${API_BASE_URL}/admin/grades/${gradeId}`);
    return response.data;
  },

  // Get grade subjects
  getSubjects: async (gradeId: string) => {
    const response = await axios.get(`${API_BASE_URL}/admin/grades/${gradeId}/subjects`);
    return response.data;
  },

  // Add subject to grade
  addSubject: async (gradeId: string, data: { subject_id: string; sort_order?: number }) => {
    const response = await axios.post(`${API_BASE_URL}/admin/grades/${gradeId}/subjects`, data);
    return response.data;
  },

  // Remove subject from grade
  removeSubject: async (gradeId: string, subjectId: string) => {
    const response = await axios.delete(`${API_BASE_URL}/admin/grades/${gradeId}/subjects/${subjectId}`);
    return response.data;
  },
};

// Subject API
export const subjectApi = {
  // List subjects
  list: async (params?: { category?: string; active_only?: boolean }) => {
    const response = await axios.get(`${API_BASE_URL}/admin/subjects`, { params });
    return response.data;
  },

  // Create subject
  create: async (data: { name: string; code: string; category: string; sort_order?: number; description?: string }) => {
    const response = await axios.post(`${API_BASE_URL}/admin/subjects`, data);
    return response.data;
  },

  // Get subject
  get: async (subjectId: string) => {
    const response = await axios.get(`${API_BASE_URL}/admin/subjects/${subjectId}`);
    return response.data;
  },

  // Update subject
  update: async (subjectId: string, data: { name?: string; category?: string; sort_order?: number; description?: string; status?: string }) => {
    const response = await axios.put(`${API_BASE_URL}/admin/subjects/${subjectId}`, data);
    return response.data;
  },

  // Delete subject
  delete: async (subjectId: string) => {
    const response = await axios.delete(`${API_BASE_URL}/admin/subjects/${subjectId}`);
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
