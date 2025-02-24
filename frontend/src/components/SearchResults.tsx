import React from 'react';
import {
  Box,
  Typography,
  Paper,
  Chip,
  IconButton,
  Grid,
  Divider,
  Collapse
} from '@mui/material';
import {
  ContentCopy as CopyIcon,
  OpenInNew as OpenInNewIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon
} from '@mui/icons-material';
import { SearchResult } from '../services/api';
import { showNotification } from '../utils/notification';

interface SearchResultsProps {
  results: SearchResult[];
  loading?: boolean;
  error?: string | null;
}

export const SearchResults: React.FC<SearchResultsProps> = ({ results, loading, error }) => {
  const [expandedResults, setExpandedResults] = React.useState<Record<number, boolean>>({});

  const handleCopy = (content: string) => {
    navigator.clipboard.writeText(content);
  };

  const toggleExpand = (index: number) => {
    setExpandedResults(prev => ({
      ...prev,
      [index]: !prev[index]
    }));
  };

  const getScoreColor = (score: number) => {
    if (score >= 0.7) return 'success';
    if (score >= 0.4) return 'warning';
    return 'error';
  };

  if (loading) {
    return <Typography>Loading results...</Typography>;
  }

  if (error) {
    return <Typography color="error">{error}</Typography>;
  }

  return (
    <Paper elevation={0} sx={{ mt: 2 }}>
      <Box sx={{ p: 2 }}>
        {results.map((result, index) => (
          <Paper 
            key={`${result.url}-${index}`} 
            elevation={1} 
            sx={{ 
              p: 2, 
              mb: 2,
              bgcolor: 'background.paper',
              '&:hover': {
                bgcolor: 'action.hover'
              }
            }}
          >
            <Grid container justifyContent="space-between" alignItems="flex-start">
              <Grid item xs>
                <Typography variant="subtitle1" gutterBottom>
                  {result.title || result.url}
                </Typography>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  {result.url}
                </Typography>
                <Box sx={{ display: 'flex', gap: 1, mt: 1 }}>
                  <Chip 
                    label={`Score: ${result.score.toFixed(2)}`}
                    size="small"
                    color={getScoreColor(result.score)}
                  />
                </Box>
              </Grid>

              <Grid item>
                <Box sx={{ display: 'flex', gap: 1 }}>
                  <IconButton 
                    size="small"
                    onClick={() => handleCopy(result.content || result.url)}
                    title="Copy Content"
                  >
                    <CopyIcon fontSize="small" />
                  </IconButton>
                  <IconButton
                    size="small"
                    component="a"
                    href={result.url}
                    target="_blank"
                    title="Open in new tab"
                  >
                    <OpenInNewIcon fontSize="small" />
                  </IconButton>
                  <IconButton
                    size="small"
                    onClick={() => toggleExpand(index)}
                    title={expandedResults[index] ? "Show less" : "Show more"}
                  >
                    {expandedResults[index] ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                  </IconButton>
                </Box>
              </Grid>
            </Grid>

            <Collapse in={expandedResults[index]}>
              <Divider sx={{ my: 2 }} />
              
              {result.content && (
                <Box sx={{ mt: 2 }}>
                  <Typography variant="body2" color="text.secondary">
                    Content Preview:
                  </Typography>
                  <Box 
                    sx={{ 
                      mt: 1,
                      maxHeight: '200px',
                      overflowY: 'auto',
                      bgcolor: 'background.paper',
                      p: 2,
                      borderRadius: 1,
                      border: '1px solid',
                      borderColor: 'divider'
                    }}
                  >
                    <Typography variant="body2" component="pre" sx={{ whiteSpace: 'pre-wrap' }}>
                      {result.content}
                    </Typography>
                  </Box>
                </Box>
              )}

              {result.metadata && Object.keys(result.metadata).length > 0 && (
                <Box sx={{ mt: 2 }}>
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    Metadata:
                  </Typography>
                  <Grid container spacing={2} sx={{ mt: 1 }}>
                    {Object.entries(result.metadata).map(([key, value]) => (
                      <Grid item xs={12} sm={4} key={key}>
                        <Box sx={{ 
                          p: 1, 
                          bgcolor: 'background.default',
                          borderRadius: 1,
                          height: '100%'
                        }}>
                          <Typography variant="body2" component="span" fontWeight="bold">
                            {key}:
                          </Typography>
                          <Typography variant="body2" component="span" sx={{ ml: 1 }}>
                            {String(value)}
                          </Typography>
                        </Box>
                      </Grid>
                    ))}
                  </Grid>
                </Box>
              )}

              {result.error && (
                <Typography color="error" variant="body2" sx={{ mt: 1 }}>
                  Error: {result.error}
                </Typography>
              )}
            </Collapse>
          </Paper>
        ))}
      </Box>
    </Paper>
  );
}; 