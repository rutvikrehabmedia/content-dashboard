import React, { useState } from 'react';
import {
  Box,
  Typography,
  Paper,
  Chip,
  IconButton,
  Collapse,
  Divider,
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
} from '@mui/icons-material';
import { BulkSearchLog } from '../services/api';
import { getStatusChipColor } from '../utils/statusUtils';
import { SearchResultCard } from './SearchResultCard';

interface BulkSearchResultsProps {
  log: BulkSearchLog;
}

export const BulkSearchResults: React.FC<BulkSearchResultsProps> = ({ log }) => {
  const [expandedQueries, setExpandedQueries] = useState<Record<string, boolean>>({});

  const handleToggleQuery = (queryId: string) => {
    setExpandedQueries(prev => ({
      ...prev,
      [queryId]: !prev[queryId]
    }));
  };

  return (
    <Box>
      {log.children?.map((child) => (
        <Paper 
          key={child.process_id} 
          variant="outlined" 
          sx={{ mb: 2 }}
        >
          <Box 
            sx={{ 
              p: 2, 
              cursor: 'pointer',
              '&:hover': { bgcolor: 'action.hover' }
            }}
            onClick={() => handleToggleQuery(child.process_id)}
          >
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Box>
                <Typography variant="subtitle1">{child.query}</Typography>
                <Typography variant="body2" color="text.secondary">
                  {child.metadata && (
                    <>
                      {child.metadata.total_results} results, {child.metadata.scraped_results} scraped
                    </>
                  )}
                </Typography>
              </Box>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Chip 
                  label={child.status} 
                  color={getStatusChipColor(child.status)} 
                  size="small" 
                />
                <IconButton size="small">
                  {expandedQueries[child.process_id] ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                </IconButton>
              </Box>
            </Box>
          </Box>

          <Collapse in={expandedQueries[child.process_id]}>
            <Divider />
            <Box sx={{ p: 2 }}>
              {child.error ? (
                <Typography color="error">{child.error}</Typography>
              ) : child.results?.length ? (
                child.results.map((result, idx) => (
                  <SearchResultCard 
                    key={idx}
                    result={result}
                  />
                ))
              ) : (
                <Typography color="text.secondary">No results found</Typography>
              )}
            </Box>
          </Collapse>
        </Paper>
      ))}
    </Box>
  );
}; 