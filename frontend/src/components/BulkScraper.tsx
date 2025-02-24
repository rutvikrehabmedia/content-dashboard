import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { searchAPI } from '../services/api';
import { Button, TextField, Paper, Typography, Box } from '@mui/material';

export const BulkScraper: React.FC = () => {
  const [urls, setUrls] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [processId, setProcessId] = useState<string | null>(null);

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    try {
      setLoading(true);
      setError(null);
      
      const file = acceptedFiles[0];
      const formData = new FormData();
      formData.append('file', file);
      
      const response = await searchAPI.uploadBulkScrape(formData);
      setProcessId(response.process_id);
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to upload file');
    } finally {
      setLoading(false);
    }
  }, []);

  const { getRootProps, getInputProps } = useDropzone({
    onDrop,
    accept: {
      'text/csv': ['.csv']
    }
  });

  const handleSubmit = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const urlList = urls.split('\n').map(url => url.trim()).filter(Boolean);
      const response = await searchAPI.bulkScrape(urlList);
      setProcessId(response.process_id);
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start bulk scrape');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h5" gutterBottom>
        Bulk Scraper
      </Typography>
      
      <Paper {...getRootProps()} sx={{ p: 3, mb: 3, textAlign: 'center' }}>
        <input {...getInputProps()} />
        <Typography>
          Drag & drop a CSV file here, or click to select one
        </Typography>
      </Paper>

      <Typography variant="h6" gutterBottom>
        Or enter URLs manually (one per line)
      </Typography>
      
      <TextField
        multiline
        rows={6}
        fullWidth
        value={urls}
        onChange={(e) => setUrls(e.target.value)}
        placeholder="Enter URLs here..."
        sx={{ mb: 2 }}
      />
      
      <Button
        variant="contained"
        onClick={handleSubmit}
        disabled={loading || !urls.trim()}
      >
        Start Bulk Scrape
      </Button>

      {error && (
        <Typography color="error" sx={{ mt: 2 }}>
          {error}
        </Typography>
      )}

      {processId && (
        <Typography sx={{ mt: 2 }}>
          Bulk scrape started! Process ID: {processId}
        </Typography>
      )}
    </Box>
  );
}; 