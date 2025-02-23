import { LogEntry, SearchResult } from '../services/api';

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

export const exportToCSV = (log: LogEntry) => {
  const results = log.results || [];
  
  const headers = [
    'URL',
    'Title',
    'Score',
    'Content',
    'Language',
    'Word Count',
    'Published Date',
    'Author',
    'Description',
    'Additional Metadata'
  ];

  const csvRows = results.map(result => {
    const data = typeof result.url === 'object' ? result.url : result;
    const metadata = data.metadata || {};
    
    return [
      formatCSVField(data.url),
      formatCSVField(data.title),
      formatCSVField(data.score),
      formatCSVField(data.content?.replace(/\n/g, ' ')),
      formatCSVField(metadata.language),
      formatCSVField(metadata.word_count),
      formatCSVField(metadata.published_date),
      formatCSVField(metadata.author),
      formatCSVField(metadata.description),
      formatCSVField((() => {
        const { language, word_count, published_date, author, description, ...rest } = metadata;
        return Object.keys(rest).length > 0 ? rest : '';
      })())
    ].join(',');
  });

  const csvContent = [headers.join(','), ...csvRows].join('\n');
  downloadFile(csvContent, `search-results-${log._id}.csv`, 'text/csv;charset=utf-8');
};

export const exportToJSON = (log: LogEntry) => {
  const exportData = {
    query: log.query,
    timestamp: log.timestamp,
    process_id: log.process_id,
    status: log.status,
    results: log.results?.map(result => {
      const data = typeof result.url === 'object' ? result.url : result;
      return {
        url: data.url,
        title: data.title,
        score: data.score,
        content: data.content,
        metadata: data.metadata
      };
    })
  };

  downloadFile(
    JSON.stringify(exportData, null, 2),
    `search-results-${log._id}.json`,
    'application/json'
  );
};

const downloadFile = (content: string, filename: string, type: string) => {
  const blob = new Blob(['\ufeff' + content], { type });
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.click();
  window.URL.revokeObjectURL(url);
}; 