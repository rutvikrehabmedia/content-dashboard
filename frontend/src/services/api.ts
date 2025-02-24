import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';
const API_TOKEN = import.meta.env.VITE_API_TOKEN || 'test-token';
export const MAX_RESULTS = Number(import.meta.env.VITE_MAX_RESULTS_PER_QUERY) || 2;

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
    'x-token': API_TOKEN
  }
});

export interface SearchRequest {
  query: string;
  whitelist?: string[];
  blacklist?: string[];
  globalListsEnabled?: boolean;
}

export interface SearchResult {
  url: string;
  title?: string;
  content?: string;
  score?: number;
  error?: string;
  metadata?: {
    title?: string;
    description?: string;
    published_date?: string;
    author?: string;
    word_count?: number;
    language?: string;
    [key: string]: any;
  };
}

export interface SearchResponse {
  results: SearchResult[];
  process_id: string;
  total_results: number;
  scraped_results: number;
}

export interface LogEntry {
  process_id: string;
  query: string;
  status: string;
  timestamp: string;
  results?: any[];
  error?: string;
  metadata?: {
    progress?: {
      total: number;
      completed: number;
      failed: number;
    };
  };
  child_logs?: LogEntry[];
}

export interface BulkSearchLog extends LogEntry {
  children?: LogEntry[];
  progress?: {
    total: number;
    completed: number;
    failed: number;
  };
}

export interface GetLogsResponse {
  logs: LogEntry[];
  total: number;
  page: number;
  per_page: number;
}

export interface BulkSearchQuery {
  query: string;
  whitelist?: string[];
  blacklist?: string[];
}

export interface BulkSearchRequest {
  queries: BulkSearchQuery[];
  globalListsEnabled: boolean;
  globalWhitelist: string[];
  globalBlacklist: string[];
}

export interface SearchSettings {
  maxResultsPerQuery: number;
  searchResultsLimit: number;
  scrapeLimit: number;
  minScoreThreshold: number;
  jinaRateLimit: number;
  searchRateLimit: number;
}

export interface ScrapeLogsResponse {
  logs: any[];
  total: number;
  page: number;
  per_page: number;
}

export const searchAPI = {
  search: async (request: SearchRequest): Promise<SearchResponse> => {
    const response = await api.post('/search', {
      ...request,
      max_results: MAX_RESULTS
    });
    return response.data;
  },

  getLogs: async (page: number = 1, perPage: number = 50): Promise<GetLogsResponse> => {
    try {
      const response = await api.get(`/logs?page=${page}&per_page=${perPage}`);
      return response.data;
    } catch (err) {
      console.error('Failed to fetch logs:', err);
      throw err;
    }
  },

  getWhitelist: async (): Promise<{ urls: string[] }> => {
    try {
      const response = await api.get('/whitelist');
      return response.data;
    } catch (err) {
      console.error('Failed to fetch whitelist:', err);
      throw new Error('Failed to fetch whitelist');
    }
  },

  updateWhitelist: async (urls: string[]): Promise<{ urls: string[] }> => {
    try {
      // Always send an array, even if empty
      const urlsToUpdate = Array.isArray(urls) ? urls : [];
      
      const response = await api.post('/whitelist', { 
        urls: urlsToUpdate 
      });
      return response.data;
    } catch (err) {
      if (axios.isAxiosError(err)) {
        const errorMessage = err.response?.data?.detail || 'Failed to update whitelist';
        throw new Error(errorMessage);
      }
      throw new Error('Failed to update whitelist');
    }
  },

  getBlacklist: async (): Promise<{ urls: string[] }> => {
    try {
      const response = await api.get('/blacklist');
      return response.data;
    } catch (err) {
      console.error('Failed to fetch blacklist:', err);
      throw new Error('Failed to fetch blacklist');
    }
  },

  updateBlacklist: async (urls: string[]): Promise<{ urls: string[] }> => {
    try {
      // Always send an array, even if empty
      const urlsToUpdate = Array.isArray(urls) ? urls : [];
      
      const response = await api.post('/blacklist', { 
        urls: urlsToUpdate 
      });
      return response.data;
    } catch (err) {
      if (axios.isAxiosError(err)) {
        const errorMessage = err.response?.data?.detail || 'Failed to update blacklist';
        throw new Error(errorMessage);
      }
      throw new Error('Failed to update blacklist');
    }
  },

  scrapeUrl: async (url: string) => {
    const response = await fetch(`${API_BASE_URL}/scrape?url=${encodeURIComponent(url)}`, {
      method: 'POST',
      headers: {
        'x-token': API_TOKEN,
        'Content-Type': 'application/json',
      }
    });

    if (!response.ok) {
      throw new Error('Failed to scrape URL');
    }

    return response.json();
  },

  bulkSearch: async (request: BulkSearchRequest): Promise<SearchResponse> => {
    try {
      // Format queries to match backend expectation
      const formattedRequest = {
        ...request,
        queries: request.queries.map(q => ({
          query: q.query.trim(),
          whitelist: q.whitelist || [],
          blacklist: q.blacklist || []
        }))
      };

      const response = await api.post('/bulk-search', formattedRequest);
      return response.data;
    } catch (err) {
      console.error('Bulk search error:', err);
      throw err;
    }
  },

  bulkScrape: async (urls: string[]): Promise<{ process_id: string }> => {
    const response = await api.post('/bulk-scrape', { urls });
    return response.data;
  },

  uploadBulkScrape: async (formData: FormData): Promise<{ process_id: string }> => {
    const response = await api.post('/bulk-scrape/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  getScrapeLogs: async (page: number = 1, perPage: number = 50): Promise<ScrapeLogsResponse> => {
    const response = await api.get(`/scrape/logs?page=${page}&per_page=${perPage}`);
    return response.data;
  },

  updateSettings: async (settings: SearchSettings): Promise<void> => {
    try {
      await api.post('/settings', settings);
    } catch (err) {
      console.error('Failed to update settings:', err);
      throw new Error('Failed to update settings');
    }
  },

  getSettings: async (): Promise<SearchSettings> => {
    try {
      const response = await api.get('/settings');
      return response.data;
    } catch (err) {
      console.error('Failed to fetch settings:', err);
      throw new Error('Failed to fetch settings');
    }
  }
}; 