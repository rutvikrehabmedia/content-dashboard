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

export const exportToCSV = (data: ExportData | ExportData[], filename: string = 'export') => {
  try {
    // Handle both array (bulk) and single object formats
    const dataArray = Array.isArray(data) ? data : [data];
    
    // Get all possible headers from all results
    const headers = new Set<string>();
    dataArray.forEach(item => {
      Object.keys(item).forEach(key => {
        if (key === 'results') {
          item.results?.forEach(result => {
            Object.keys(result).forEach(resultKey => headers.add(resultKey));
          });
        } else {
          headers.add(key);
        }
      });
    });

    // Create CSV content
    let csv = Array.from(headers).join(',') + '\n';

    dataArray.forEach(item => {
      if (item.results && item.results.length > 0) {
        // Export each result as a row
        item.results.forEach(result => {
          const row = Array.from(headers).map(header => {
            if (header in result) {
              return formatCSVField(result[header as keyof typeof result]);
            }
            return formatCSVField(item[header as keyof typeof item]);
          });
          csv += row.join(',') + '\n';
        });
      } else {
        // Export log info without results
        const row = Array.from(headers).map(header => 
          formatCSVField(item[header as keyof typeof item])
        );
        csv += row.join(',') + '\n';
      }
    });

    // Create and save file
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    saveAs(blob, `${filename}.csv`);
  } catch (error) {
    console.error('Error exporting to CSV:', error);
  }
};

export const exportToJSON = (data: ExportData | ExportData[], filename: string = 'export') => {
  try {
    const blob = new Blob(
      [JSON.stringify(data, null, 2)], 
      { type: 'application/json' }
    );
    saveAs(blob, `${filename}.json`);
  } catch (error) {
    console.error('Error exporting to JSON:', error);
  }
}; 