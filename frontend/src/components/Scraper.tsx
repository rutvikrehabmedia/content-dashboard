import React, { useState } from 'react';
import {
  Box,
  Container,
  Typography,
  Paper,
  TextField,
  Button,
  Card,
  CardContent,
  Grid,
  CircularProgress,
  Alert,
  IconButton,
  Tooltip,
  Divider
} from '@mui/material';
import {
  ContentCopy as CopyIcon,
  OpenInNew as OpenInNewIcon,
  Download as DownloadIcon
} from '@mui/icons-material';
import { searchAPI } from '../services/api';

export const Scraper = () => {
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const handleScrape = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // TODO: Implement scraping API endpoint
      const response = await searchAPI.scrapeUrl(url);
      setResult(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const handleCopyContent = (content: string) => {
    navigator.clipboard.writeText(content);
  };

  return (
    <Container maxWidth="xl">
      <Paper 
        elevation={0} 
        sx={{ 
          p: 4, 
          mb: 4, 
          bgcolor: 'primary.main',
          color: 'white'
        }}
      >
        <Typography variant="h4" gutterBottom>
          Web Scraper
        </Typography>
        <Typography variant="subtitle1">
          Extract content from any webpage with intelligent parsing
        </Typography>
      </Paper>

      <Card sx={{ mb: 4 }}>
        <CardContent>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} md={9}>
              <TextField
                fullWidth
                label="URL to Scrape"
                variant="outlined"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                disabled={loading}
                placeholder="Enter webpage URL (e.g., https://example.com)"
              />
            </Grid>
            <Grid item xs={12} md={3}>
              <Button
                fullWidth
                variant="contained"
                onClick={handleScrape}
                disabled={loading || !url.trim()}
                startIcon={loading ? <CircularProgress size={20} /> : <DownloadIcon />}
                size="large"
              >
                Scrape Content
              </Button>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {result && (
        <Card>
          <CardContent>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
              <Typography variant="h6" component="div" sx={{ color: 'primary.main' }}>
                {result.metadata?.title || result.url}
              </Typography>
              <Box>
                <Tooltip title="Copy URL">
                  <IconButton size="small" onClick={() => handleCopyContent(result.url)}>
                    <CopyIcon />
                  </IconButton>
                </Tooltip>
                <Tooltip title="Open in new tab">
                  <IconButton size="small" href={result.url} target="_blank">
                    <OpenInNewIcon />
                  </IconButton>
                </Tooltip>
              </Box>
            </Box>

            <Divider sx={{ my: 2 }} />

            <Box sx={{ mt: 3 }}>
              <Typography variant="subtitle2" gutterBottom>
                Extracted Content
              </Typography>
              <Paper 
                sx={{ 
                  p: 2, 
                  maxHeight: '400px', 
                  overflow: 'auto',
                  bgcolor: 'grey.50',
                  position: 'relative'
                }}
              >
                <Tooltip title="Copy Content">
                  <IconButton 
                    size="small" 
                    onClick={() => handleCopyContent(result.content)}
                    sx={{ position: 'absolute', top: 8, right: 8 }}
                  >
                    <CopyIcon />
                  </IconButton>
                </Tooltip>
                <Typography 
                  variant="body2" 
                  component="pre"
                  sx={{ 
                    whiteSpace: 'pre-wrap',
                    wordBreak: 'break-word',
                    fontFamily: 'monospace'
                  }}
                >
                  {result.content}
                </Typography>
              </Paper>
            </Box>

            {result.metadata && (
              <Box sx={{ mt: 3 }}>
                <Typography variant="subtitle2" gutterBottom>
                  Metadata
                </Typography>
                <Grid container spacing={2}>
                  {Object.entries(result.metadata).map(([key, value]) => (
                    <Grid item xs={12} sm={6} md={4} key={key}>
                      <Paper sx={{ p: 2 }}>
                        <Typography variant="caption" color="text.secondary">
                          {key}
                        </Typography>
                        <Typography variant="body2">
                          {String(value)}
                        </Typography>
                      </Paper>
                    </Grid>
                  ))}
                </Grid>
              </Box>
            )}
          </CardContent>
        </Card>
      )}
    </Container>
  );
}; 