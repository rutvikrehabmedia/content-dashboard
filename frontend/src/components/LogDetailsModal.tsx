import React from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Box,
  Typography,
  Chip,
  CircularProgress,
} from '@mui/material';
import { BulkSearchLog } from '../services/api';
import { getStatusChipColor } from '../utils/statusUtils';
import { BulkSearchResults } from './BulkSearchResults';
import { SearchResultCard } from './SearchResultCard';

interface LogDetailsModalProps {
  open: boolean;
  onClose: () => void;
  log: BulkSearchLog | null;
  loading: boolean;
}

export const LogDetailsModal: React.FC<LogDetailsModalProps> = ({
  open,
  onClose,
  log,
  loading
}) => {
  const isBulkSearch = log?.query === 'BULK_SEARCH';
  
  // Get child_logs from the API response
  const childLogs = log?.child_logs || [];

  return (
    <Dialog 
      open={open} 
      onClose={onClose}
      maxWidth="md"
      fullWidth
    >
      <DialogTitle>
        <Box sx={{ mb: 2 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
            <Typography variant="h6">
              {isBulkSearch ? 'Bulk Search' : log?.query}
            </Typography>
            <Chip 
              label={log?.status} 
              color={getStatusChipColor(log?.status || '')}
            />
          </Box>
          <Typography variant="body2" color="text.secondary">
            Process ID: {log?.process_id}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Time: {log?.timestamp && new Date(log.timestamp).toLocaleString()}
          </Typography>
        </Box>

        {isBulkSearch && log?.progress && (
          <Box sx={{ mb: 2 }}>
            <Typography variant="subtitle1" gutterBottom>Progress</Typography>
            <Typography variant="body2">
              {log.progress.completed} completed, {log.progress.failed} failed
              {log.progress.total > 0 && `, ${log.progress.total - log.progress.completed - log.progress.failed} pending`}
            </Typography>
          </Box>
        )}

        {!isBulkSearch && log?.metadata && (
          <Box sx={{ mb: 2 }}>
            <Typography variant="subtitle1" gutterBottom>Results Summary</Typography>
            <Typography variant="body2">
              Total Results: {log.metadata.total_results || 0}
            </Typography>
            <Typography variant="body2">
              Scraped Results: {log.metadata.scraped_results || 0}
            </Typography>
          </Box>
        )}
      </DialogTitle>

      <DialogContent dividers>
        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
            <CircularProgress />
          </Box>
        ) : isBulkSearch ? (
          childLogs && childLogs.length > 0 ? (
            <BulkSearchResults log={{...log, children: childLogs}} />
          ) : (
            <Typography color="text.secondary" align="center">
              No results found
            </Typography>
          )
        ) : (
          log?.results && log.results.length > 0 ? (
            <Box>
              {log.results.map((result, index) => (
                <SearchResultCard 
                  key={index}
                  result={result}
                />
              ))}
            </Box>
          ) : (
            <Typography color="text.secondary" align="center">
              No results found
            </Typography>
          )
        )}
      </DialogContent>

      <DialogActions>
        <Button onClick={onClose}>Close</Button>
      </DialogActions>
    </Dialog>
  );
}; 