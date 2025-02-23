import React, { useEffect, useState, useRef } from 'react';
import {
  Box,
  Container,
  Typography,
  Paper,
  IconButton,
  Tooltip,
  Alert
} from '@mui/material';
import { Refresh as RefreshIcon } from '@mui/icons-material';
import { searchAPI, LogEntry } from '../services/api';
import { LogCard } from './LogCard';
import { BulkSearchLog } from '../services/api';

export interface GetLogsResponse {
  logs: LogEntry[];
  total: number;
  page: number;
  per_page: number;
}

const Logs: React.FC = () => {
  const [logs, setLogs] = useState<BulkSearchLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [page, setPage] = useState(1);
  const PER_PAGE = 50; // Limit to 10 logs per page
  const [hasMore, setHasMore] = useState(true);
  const refreshTimeoutRef = useRef<NodeJS.Timeout>();

  const fetchLogs = async (isAutoRefresh = false) => {
    try {
      if (!isAutoRefresh) {
        setLoading(true);
      }
      setRefreshing(true);

      const response = await searchAPI.getLogs(page, PER_PAGE);

      // Process logs; filter out logs with status 'started',
      // group bulk searches (and sort children by timestamp),
      // then sort the parent logs (latest first)
      const processedLogs = response.logs
        .reduce((acc: BulkSearchLog[], log: LogEntry) => {
          if (log.status === 'started') return acc;

          if (log.query === 'BULK_SEARCH') {
            const children = response.logs
              .filter(childLog => childLog.parent_process_id === log.process_id)
              .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
            const total = children.length;
            const completed = children.filter(c => c.status === 'completed').length;
            const failed = children.filter(c => c.status === 'failed').length;

            acc.push({
              ...log,
              children,
              progress: { total, completed, failed },
              status: completed + failed === total ? 'completed' : 'processing'
            });
          } else if (!log.parent_process_id) {
            acc.push(log as BulkSearchLog);
          }
          return acc;
        }, [])
        .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());

      setLogs(isAutoRefresh
        ? mergeAndDedupeLogs(logs, processedLogs)
        : processedLogs
      );
      setHasMore(response.total > page * PER_PAGE);

      // Auto-refresh if any log is still processing
      const hasProcessingLogs = processedLogs.some(
        log => log.status === 'processing'
      );
      if (hasProcessingLogs) {
        if (refreshTimeoutRef.current) {
          clearTimeout(refreshTimeoutRef.current);
        }
        refreshTimeoutRef.current = setTimeout(() => fetchLogs(true), 5000);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch logs');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  // Helper: merge and deduplicate logs
  const mergeAndDedupeLogs = (oldLogs: BulkSearchLog[], newLogs: BulkSearchLog[]): BulkSearchLog[] => {
    const merged = [...oldLogs];
    newLogs.forEach(newLog => {
      const index = merged.findIndex(log => log._id === newLog._id);
      if (index >= 0) {
        merged[index] = newLog;
      } else {
        merged.unshift(newLog);
      }
    });
    return merged;
  };

  useEffect(() => {
    fetchLogs();
    return () => {
      if (refreshTimeoutRef.current) {
        clearTimeout(refreshTimeoutRef.current);
      }
    };
  }, [page]);

  const handleRefresh = () => {
    setPage(1);
    fetchLogs();
  };

  return (
    <Container maxWidth="xl">
      <Paper elevation={0} sx={{ p: 4, mb: 4, bgcolor: 'primary.main', color: 'white' }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <Typography variant="h4" gutterBottom>
              Search &amp; Scraping Logs
            </Typography>
            <Typography variant="subtitle1">
              View and export your search and scraping history
            </Typography>
          </div>
          <Tooltip title="Refresh Logs">
            <IconButton
              onClick={handleRefresh}
              sx={{ color: 'white' }}
              disabled={refreshing}
            >
              <RefreshIcon />
            </IconButton>
          </Tooltip>
        </Box>
      </Paper>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {loading && logs.length === 0 ? (
        <Typography>Loading logs...</Typography>
      ) : (
        logs.map(log => (
          <LogCard key={log._id} log={log} onRefresh={handleRefresh} />
        ))
      )}
    </Container>
  );
};

export default Logs; 