import React from 'react';
import { Box, Typography, Paper, Link, Chip } from '@mui/material';
import { SearchResult } from '../services/api';
import { RelevanceScore } from './RelevanceScore';

interface SearchResultsProps {
  results: SearchResult[];
  query: string;
  loading: boolean;
  error?: string | null;
  compact?: boolean;
}

export const SearchResults: React.FC<SearchResultsProps> = ({
  results,
  loading,
  error,
  compact = false
}) => {
  if (loading) {
    return <Typography>Loading results...</Typography>;
  }

  if (error) {
    return <Typography color="error">{error}</Typography>;
  }

  if (!results || results.length === 0) {
    return <Typography>No results found</Typography>;
  }

  return (
    <Box>
      {results.map((result, index) => {
        const data = typeof result.url === 'object' ? result.url : result;
        
        return (
          <Paper 
            key={index} 
            sx={{ 
              p: compact ? 1 : 2, 
              mb: 2,
              bgcolor: 'background.paper' 
            }}
          >
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
              <Link 
                href={data.url} 
                target="_blank" 
                rel="noopener noreferrer"
                sx={{ 
                  color: 'primary.main',
                  fontWeight: 'medium',
                  textDecoration: 'none',
                  '&:hover': {
                    textDecoration: 'underline'
                  }
                }}
              >
                {data.title || data.url}
              </Link>
              {data.score !== undefined && (
                <RelevanceScore score={data.score} />
              )}
            </Box>

            {!compact && data.content && (
              <Typography 
                variant="body2" 
                color="text.secondary"
                sx={{ 
                  mb: 1,
                  display: '-webkit-box',
                  WebkitLineClamp: 3,
                  WebkitBoxOrient: 'vertical',
                  overflow: 'hidden'
                }}
              >
                {data.content}
              </Typography>
            )}

            {data.metadata && (
              <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                {Object.entries(data.metadata).map(([key, value]) => (
                  <Chip
                    key={key}
                    label={`${key}: ${value}`}
                    size="small"
                    variant="outlined"
                  />
                ))}
              </Box>
            )}
          </Paper>
        );
      })}
    </Box>
  );
}; 