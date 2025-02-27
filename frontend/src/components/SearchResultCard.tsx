import React, { useState } from 'react';
import {
  Box,
  Typography,
  Paper,
  Chip,
  IconButton,
  Link,
  Collapse,
  Divider
} from '@mui/material';
import {
  ContentCopy as CopyIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
} from '@mui/icons-material';
import { SearchResult } from '../services/api';

interface SearchResultCardProps {
  result: SearchResult;
}

export const SearchResultCard: React.FC<SearchResultCardProps> = ({ result }) => {
  const [expanded, setExpanded] = useState(false);

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  return (
    <Paper variant="outlined" sx={{ mb: 1, overflow: 'hidden' }}>
      <Box 
        sx={{ 
          p: 2, 
          cursor: 'pointer',
          '&:hover': { bgcolor: 'action.hover' }
        }}
        onClick={() => setExpanded(!expanded)}
      >
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Box>
            <Link 
              href={result.url} 
              target="_blank"
              rel="noopener noreferrer"
              onClick={(e) => e.stopPropagation()}
              sx={{ color: 'primary.main', fontWeight: 'medium' }}
            >
              {result.title || result.url}
            </Link>
            {result.score !== undefined && (
              <Chip 
                label={`Score: ${result.score.toFixed(2)}`}
                size="small"
                color={result.score > 0.7 ? "success" : "default"}
                sx={{ ml: 1 }}
              />
            )}
          </Box>
          <IconButton size="small">
            {expanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
          </IconButton>
        </Box>
      </Box>

      <Collapse in={expanded}>
        <Divider />
        <Box sx={{ p: 2 }}>
          {result.content && (
            <Box sx={{ mb: 2 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                <Typography variant="subtitle2">Content</Typography>
                <IconButton 
                  size="small" 
                  onClick={() => handleCopy(result.content!)}
                >
                  <CopyIcon fontSize="small" />
                </IconButton>
              </Box>
              <Box sx={{ 
                bgcolor: 'grey.50',
                p: 1.5,
                borderRadius: 1,
                maxHeight: 200,
                overflow: 'auto'
              }}>
                <Typography variant="body2">{result.content}</Typography>
              </Box>
            </Box>
          )}

          {result.metadata && Object.keys(result.metadata).length > 0 && (
            <Box>
              <Typography variant="subtitle2" sx={{ mb: 1 }}>Metadata</Typography>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                {Object.entries(result.metadata).map(([key, value]) => (
                  value && (
                    <Chip
                      key={key}
                      label={`${key}: ${value}`}
                      size="small"
                      variant="outlined"
                    />
                  )
                ))}
              </Box>
            </Box>
          )}
        </Box>
      </Collapse>
    </Paper>
  );
}; 