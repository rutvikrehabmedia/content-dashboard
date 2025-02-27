import React, { useState } from 'react';
import {
  Box,
  Typography,
  Paper,
  Chip,
  IconButton,
  Button,
  Menu,
  MenuItem,
  LinearProgress,
} from '@mui/material';
import {
  ContentCopy as CopyIcon,
  FileDownload as FileDownloadIcon,
  OpenInNew as OpenInNewIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';
import { BulkSearchLog } from '../services/api';
import { getStatusChipColor } from '../utils/statusUtils';
import { exportToCSV, exportToJSON } from '../utils/exportUtils';

interface LogCardProps {
  log: BulkSearchLog;
  onRefresh: () => void;
  onViewDetails: () => void;
  loadingDetails?: boolean;
}

export const LogCard: React.FC<LogCardProps> = ({ 
  log, 
  onRefresh, 
  onViewDetails,
  loadingDetails = false
}) => {
  const [exportMenu, setExportMenu] = useState<null | HTMLElement>(null);
  const isBulkSearch = log.query === 'BULK_SEARCH';

  const handleExportClick = (event: React.MouseEvent<HTMLElement>) => {
    setExportMenu(event.currentTarget);
  };

  const handleExport = (format: 'csv' | 'json') => {
    const exportData = isBulkSearch && log.child_logs ? 
      log.child_logs.map(childLog => ({
        process_id: childLog.process_id,
        query: childLog.query,
        timestamp: childLog.timestamp,
        status: childLog.status,
        results: childLog.results,
        metadata: childLog.metadata,
        error: childLog.error
      })) : {
        process_id: log.process_id,
        query: log.query,
        timestamp: log.timestamp,
        status: log.status,
        results: log.results,
        metadata: log.metadata,
        error: log.error
      };

    if (format === 'csv') {
      exportToCSV(exportData, `search-log-${log.process_id}`);
    } else {
      exportToJSON(exportData, `search-log-${log.process_id}`);
    }
    setExportMenu(null);
  };

  const handleCopyQuery = () => {
    navigator.clipboard.writeText(log.query);
  };

  return (
    <Paper sx={{ p: 2, mb: 2 }}>
      <Box>
        {/* Header */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
          <Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
              <Typography variant="h6" component="div">
                {isBulkSearch ? 'Bulk Search' : log.query}
              </Typography>
              <IconButton size="small" onClick={handleCopyQuery}>
                <CopyIcon fontSize="small" />
              </IconButton>
            </Box>
            <Typography variant="body2" color="text.secondary">
              {new Date(log.timestamp).toLocaleString()}
            </Typography>
            {isBulkSearch && log.progress && (
              <Typography variant="body2" color="text.secondary">
                {log.progress.completed} completed, {log.progress.failed} failed
                {log.progress.total > 0 && `, ${log.progress.total - log.progress.completed - log.progress.failed} pending`}
              </Typography>
            )}
          </Box>

          <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
            <Chip 
              label={log.status} 
              color={getStatusChipColor(log.status)}
              size="small"
            />

            <Button
              startIcon={<FileDownloadIcon />}
              variant="outlined"
              size="small"
              onClick={handleExportClick}
            >
              Export
            </Button>

            <Menu
              anchorEl={exportMenu}
              open={Boolean(exportMenu)}
              onClose={() => setExportMenu(null)}
            >
              <MenuItem onClick={() => handleExport('csv')}>Export as CSV</MenuItem>
              <MenuItem onClick={() => handleExport('json')}>Export as JSON</MenuItem>
            </Menu>

            <Button
              startIcon={<RefreshIcon />}
              variant="outlined"
              size="small"
              onClick={onRefresh}
            >
              Refresh
            </Button>

            <Button
              startIcon={<OpenInNewIcon />}
              variant="contained"
              size="small"
              onClick={onViewDetails}
              disabled={loadingDetails}
            >
              View Details
            </Button>
          </Box>
        </Box>

        {/* Progress bar for bulk searches */}
        {isBulkSearch && log.progress && (
          <Box sx={{ mt: 2 }}>
            <LinearProgress 
              variant="determinate" 
              value={((log.progress.completed + log.progress.failed) / log.progress.total) * 100}
              sx={{ height: 8, borderRadius: 1 }}
            />
          </Box>
        )}
      </Box>
    </Paper>
  );
};