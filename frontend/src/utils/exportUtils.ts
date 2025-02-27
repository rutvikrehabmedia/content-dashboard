import { saveAs } from 'file-saver';
import { LogEntry } from '../services/api';

const formatCSVField = (value: any): string => {
  if (value === null || value === undefined) {
    return '';
  }
  
  const stringValue = typeof value === 'object' ? JSON.stringify(value) : String(value);
  if (stringValue.includes(',') || stringValue.includes('"') || stringValue.includes('\n')) {
    return `"${stringValue.replace(/"/g, '""')}"`;
  }
  return stringValue;
};

interface ExportData {
  process_id: string;
  query: string;
  timestamp: string;
  status: string;
  results?: Array<{
    url: string;
    title?: string;
    content?: string;
    score?: number;
    metadata?: Record<string, any>;
  }>;
  total_results?: number;
  scraped_results?: number;
  error?: string;
}

export const exportToCSV = (data: any, filename: string) => {
  let csvContent = '';
  
  // Handle array of logs (bulk search) vs single log
  const rows = Array.isArray(data) ? data : [data];
  
  // Get all possible headers from all objects
  const headers = new Set<string>();
  rows.forEach(row => {
    Object.keys(row).forEach(key => {
      if (key !== 'results') headers.add(key); // Exclude results array from main CSV
    });
    // Add result-specific headers
    if (row.results?.[0]) {
      Object.keys(row.results[0]).forEach(key => {
        headers.add(`result_${key}`);
      });
    }
  });

  // Convert headers set to array and create header row
  const headerRow = Array.from(headers);
  csvContent += headerRow.join(',') + '\n';

  // Create data rows
  rows.forEach(row => {
    const rowData = headerRow.map(header => {
      if (header.startsWith('result_')) {
        // Handle result fields
        const resultField = header.replace('result_', '');
        const results = row.results || [];
        return `"${results.map(r => r[resultField]).join('; ')}"`;
      } else if (header === 'metadata') {
        // Convert metadata object to string
        return `"${JSON.stringify(row[header] || {}).replace(/"/g, '""')}"`;
      } else {
        // Handle regular fields
        return `"${(row[header] || '').toString().replace(/"/g, '""')}"`;
      }
    });
    csvContent += rowData.join(',') + '\n';
  });

  // Create and trigger download
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  const link = document.createElement('a');
  if (link.download !== undefined) {
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', `${filename}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }
};

export const exportToJSON = (data: any, filename: string) => {
  const jsonString = JSON.stringify(data, null, 2);
  const blob = new Blob([jsonString], { type: 'application/json' });
  const link = document.createElement('a');
  
  if (link.download !== undefined) {
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', `${filename}.json`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }
}; 