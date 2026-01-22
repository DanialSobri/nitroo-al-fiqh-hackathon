import axios from 'axios';

const client = axios.create({
  baseURL: 'http://localhost:8000', // Direct API URL since we running React locally
  headers: {
    'Content-Type': 'application/json',
  },
});

export const checkHealth = async () => {
  const response = await client.get('/health');
  return response.data;
};

export const uploadContract = async (file) => {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await client.post('/contracts/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

export const checkCompliance = async (contractId) => {
  const response = await client.post(`/contracts/check-compliance/${contractId}`);
  return response.data;
};

export const getStoredReport = async (contractId) => {
  const response = await client.get(`/contracts/report/${contractId}`);
  return response.data;
};

export const getContractHistory = async () => {
  const response = await client.get('/contracts/history');
  return response.data;
};

export const rateContract = async (contractId, rating) => {
  const response = await client.post('/contracts/rate', {
    contract_id: contractId,
    rating: rating
  });
  return response.data;
};

export const getAnalytics = async () => {
  const response = await client.get('/contracts/analytics/summary');
  return response.data;
};

export const submitToScholar = async (contractId, notes = null) => {
  const response = await client.post('/contracts/submit-to-scholar', {
    contract_id: contractId,
    notes: notes
  });
  return response.data;
};

export const addRegulations = async (regulations) => {
  const response = await client.post('/regulations/bulk-add', regulations);
  return response.data;
};

export const listRegulations = async (offset = 0, limit = 20) => {
  const response = await client.get(`/regulations/list?offset=${offset}&limit=${limit}`);
  return response.data;
};

export const searchRegulations = async (query, limit = 10) => {
  const response = await client.get(`/regulations/search?query=${encodeURIComponent(query)}&limit=${limit}`);
  return response.data;
};

export default client;
