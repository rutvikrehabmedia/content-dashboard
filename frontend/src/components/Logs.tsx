import React, { useEffect, useState, useCallback } from 'react';
import {
  Box,
  Container,
  Typography,
  CircularProgress,
  Alert,
} from '@mui/material';
import { searchAPI, LogEntry, BulkSearchLog } from '../services/api';
import { LogCard } from './LogCard';
import { LogDetailsModal } from './LogDetailsModal';

const Logs: React.FC = () => {
  const [logs, setLogs] = useState<BulkSearchLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedLog, setSelectedLog] = useState<BulkSearchLog | null>(null);
  const [detailsOpen, setDetailsOpen] = useState(false);
  const [loadingDetails, setLoadingDetails] = useState(false);

  // Load logs
  const loadLogs = async () => {
    try {
      setLoading(true);
      const response = await searchAPI.getLogs();
      
      // Process logs to combine bulk search results
      const processedLogs = response.logs.reduce((acc: BulkSearchLog[], log: LogEntry) => {
        // For bulk searches, check if we have child logs in the response
        if (log.query === 'BULK_SEARCH') {
          const childLogs = response.logs.filter(
            childLog => childLog.parent_process_id === log.process_id
          );
          
          if (childLogs.length > 0) {
            // Add child logs to the bulk search log
            acc.push({
              ...log,
              children: childLogs,
              progress: {
                total: childLogs.length,
                completed: childLogs.filter(l => l.status === 'completed').length,
                failed: childLogs.filter(l => l.status === 'failed').length
              }
            });
          } else {
            acc.push(log as BulkSearchLog);
          }
        } else if (!log.parent_process_id) {
          // Only add non-child logs
          acc.push(log as BulkSearchLog);
        }
        return acc;
      }, []);

      setLogs(processedLogs);
      setError(null);
    } catch (err) {
      setError('Failed to load logs');
      console.error('Error loading logs:', err);
    } finally {
      setLoading(false);
    }
  };

  // Load details for a specific log
  const loadLogDetails = async (log: BulkSearchLog) => {
    // If it's not a bulk search or we already have details, just show the modal
    if (log.query !== 'BULK_SEARCH' || log.children?.length > 0) {
      setSelectedLog(log);
      setDetailsOpen(true);
      return;
    }

    try {
      setLoadingDetails(true);
      const details = await searchAPI.getBulkSearchDetails(log.process_id);
      
      // Update the logs state with the new details
      setLogs(prevLogs => {
        const newLogs = [...prevLogs];
        const index = newLogs.findIndex(l => l.process_id === log.process_id);
        if (index >= 0) {
          newLogs[index] = {
            ...log,
            ...details,
            children: details.children || []
          };
        }
        return newLogs;
      });

      setSelectedLog({
        ...log,
        ...details,
        children: details.children || []
      });
      setDetailsOpen(true);
    } catch (err) {
      console.error('Error loading log details:', err);
    } finally {
      setLoadingDetails(false);
    }
  };

  // Handle refresh for a specific log
  const handleRefresh = async (log: BulkSearchLog) => {
    await loadLogDetails(log);
  };

  useEffect(() => {
    loadLogs();
  }, []);

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
          <CircularProgress />
        </Box>
      ) : error ? (
        <Alert severity="error">{error}</Alert>
      ) : logs.length === 0 ? (
        <Typography align="center" color="text.secondary">
          No logs found
        </Typography>
      ) : (
        logs.map(log => (
          <LogCard 
            key={log.process_id} 
            log={log} 
            onRefresh={() => handleRefresh(log)} 
            onViewDetails={() => loadLogDetails(log)}
            loadingDetails={loadingDetails && selectedLog?.process_id === log.process_id}
          />
        ))
      )}

      <LogDetailsModal
        open={detailsOpen}
        onClose={() => setDetailsOpen(false)}
        log={selectedLog}
        loading={loadingDetails}
      />
    </Container>
  );
};

export default Logs; 