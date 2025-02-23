import React from 'react';
import {
  Box,
  Typography,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Chip,
  LinearProgress,
  Alert
} from '@mui/material';
import { ExpandMore as ExpandMoreIcon } from '@mui/icons-material';
import { BulkSearchLog, LogEntry } from '../services/api';
import { SearchResults } from './SearchResults';
import { getStatusChipColor, StatusType } from '../utils/statusUtils';

interface BulkSearchResultsProps {
  log: BulkSearchLog;
}

export const BulkSearchResults: React.FC<BulkSearchResultsProps> = ({ log }) => {
  if (!log.children?.length) {
    return (
      <Alert severity="info">
        No individual queries found
      </Alert>
    );
  }

  return (
    <Box>
      {log.children.map((childLog) => (
        <Accordion key={childLog.process_id}>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, width: '100%' }}>
              <Typography>{childLog.query}</Typography>
              <Chip
                label={`${childLog.status} ${childLog.results?.length || 0} results`}
                color={getStatusChipColor(childLog.status as StatusType)}
                size="small"
              />
              {childLog.status === 'processing' && (
                <LinearProgress 
                  sx={{ flexGrow: 1 }} 
                  variant="indeterminate" 
                />
              )}
            </Box>
          </AccordionSummary>
          <AccordionDetails>
            {childLog.error ? (
              <Alert severity="error">{childLog.error}</Alert>
            ) : childLog.status === 'processing' ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', p: 2 }}>
                <LinearProgress sx={{ width: '50%' }} />
              </Box>
            ) : !childLog.results?.length ? (
              <Alert severity="info">No results found</Alert>
            ) : (
              <SearchResults
                results={childLog.results}
                query={childLog.query}
                loading={childLog.status === 'processing'}
                compact
              />
            )}
          </AccordionDetails>
        </Accordion>
      ))}
    </Box>
  );
}; 