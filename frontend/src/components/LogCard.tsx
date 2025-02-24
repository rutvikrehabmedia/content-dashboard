import React, { useState } from 'react';
import {
  Box,
  Typography,
  Paper,
  Chip,
  IconButton,
  Tooltip,
  Button,
  Menu,
  MenuItem,
  Collapse,
  Grid,
  Divider,
  LinearProgress
} from '@mui/material';
import {
  ContentCopy as CopyIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  FileDownload as FileDownloadIcon,
} from '@mui/icons-material';
import { SearchResultCard } from './SearchResultCard';
import { exportToCSV, exportToJSON } from '../utils/exportUtils';

// Define types
interface LogCardProps {
  log: {
    process_id: string;
    query: string;
    status: string;
    timestamp: string;
    results?: any[];
    error?: string;
    metadata?: {
      progress?: {
        total: number;
        completed: number;
        failed: number;
      };
    };
    child_logs?: Array<{
      process_id: string;
      query: string;
      status: string;
      error?: string;
      results?: any[];
    }>;
  };
  onRefresh: () => void;
}

// Utility functions
const getStatusChipColor = (status: string): "default" | "primary" | "secondary" | "error" | "info" | "success" | "warning" => {
  switch (status.toLowerCase()) {
    case 'completed':
      return 'success';
    case 'failed':
    case 'error':
      return 'error';
    case 'processing':
    case 'started':
      return 'primary';
    default:
      return 'default';
  }
};

export const LogCard: React.FC<LogCardProps> = ({ log, onRefresh }) => {
  const [expanded, setExpanded] = useState(false);
  const [exportMenu, setExportMenu] = useState<null | HTMLElement>(null);

  const handleExportClick = (event: React.MouseEvent<HTMLElement>) => {
    setExportMenu(event.currentTarget);
  };

  const handleExport = (format: 'csv' | 'json') => {
    setExportMenu(null);
    if (format === 'csv') {
      exportToCSV(log);
    } else {
      exportToJSON(log);
    }
  };

  const renderProgress = () => {
    const progress = log.metadata?.progress;
    if (!progress) return null;
    
    const { total, completed, failed } = progress;
    const percentage = total > 0 ? Math.round(((completed + failed) / total) * 100) : 0;
    const isComplete = completed + failed >= total;
    const hasFailures = failed > 0;

    return (
      <Box sx={{ mt: 2, mb: 1 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
          <Typography variant="body2">
            Progress: {percentage}% {isComplete ? '(Complete)' : ''}
          </Typography>
          <Typography variant="body2">
            {completed} of {total} completed
            {failed > 0 && ` (${failed} failed)`}
          </Typography>
        </Box>
        <LinearProgress
          variant="determinate"
          value={percentage}
          color={hasFailures ? 'warning' : 'primary'}
          sx={{
            bgcolor: 'grey.200',
            '& .MuiLinearProgress-bar': {
              bgcolor: isComplete 
                ? (hasFailures ? 'warning.main' : 'success.main')
                : 'primary.main'
            }
          }}
        />
      </Box>
    );
  };

  const renderChildLogs = () => {
    if (!log.child_logs?.length) return null;

    return (
      <Box sx={{ mt: 2 }}>
        <Typography variant="subtitle1" gutterBottom>
          Individual Queries
        </Typography>
        {log.child_logs.map((childLog, index) => (
          <Paper 
            key={childLog.process_id} 
            elevation={1} 
            sx={{ 
              p: 2, 
              mb: 2,
              bgcolor: 'background.default' 
            }}
          >
            <Typography variant="subtitle2" gutterBottom>
              Query: {childLog.query}
            </Typography>
            <Chip
              label={childLog.status}
              color={getStatusChipColor(childLog.status)}
              size="small"
              sx={{ mb: 1 }}
            />
            {childLog.error && (
              <Typography color="error" variant="body2">
                Error: {childLog.error}
              </Typography>
            )}
            {childLog.results && (
              <Box sx={{ mt: 2 }}>
                <Typography variant="body2" gutterBottom>
                  Results ({childLog.results.length}):
                </Typography>
                {childLog.results.map((result, idx) => (
                  <SearchResultCard
                    key={`${childLog.process_id}-${idx}`}
                    result={result}
                    index={idx}
                    parentId={childLog.process_id}
                  />
                ))}
              </Box>
            )}
          </Paper>
        ))}
      </Box>
    );
  };

  return (
    <Paper elevation={2} sx={{ p: 2, mb: 2 }}>
      <Box>
        <Grid container justifyContent="space-between" alignItems="center">
          <Grid item>
            <Typography variant="subtitle1">
              {log.query === 'BULK_SEARCH' ? 'Bulk Search' : log.query}
              <Chip
                label={log.status}
                color={getStatusChipColor(log.status)}
                size="small"
                sx={{ ml: 1 }}
              />
            </Typography>
            <Typography variant="body2" color="text.secondary">
              ID: {log.process_id}
              <IconButton size="small" onClick={() => navigator.clipboard.writeText(log.process_id)}>
                <CopyIcon fontSize="small" />
              </IconButton>
              • {new Date(log.timestamp).toLocaleString()}
            </Typography>
          </Grid>

          <Grid item>
            <Box sx={{ display: 'flex', gap: 1 }}>
              {log.status === 'completed' && (
                <IconButton size="small" onClick={handleExportClick}>
                  <FileDownloadIcon />
                </IconButton>
              )}
              <IconButton size="small" onClick={() => setExpanded(!expanded)}>
                {expanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
              </IconButton>
            </Box>
          </Grid>
        </Grid>

        {renderProgress()}

        <Menu
          anchorEl={exportMenu}
          open={Boolean(exportMenu)}
          onClose={() => setExportMenu(null)}
        >
          <MenuItem onClick={() => handleExport('csv')}>Export as CSV</MenuItem>
          <MenuItem onClick={() => handleExport('json')}>Export as JSON</MenuItem>
        </Menu>

        <Collapse in={expanded}>
          <Divider sx={{ my: 2 }} />
          {log.query === 'BULK_SEARCH' ? renderChildLogs() : (
            <Box sx={{ maxHeight: '500px', overflowY: 'auto' }}>
              {(log.results || []).map((result, index) => (
                <SearchResultCard
                  key={`${log.process_id}-${index}`}
                  result={result}
                  index={index}
                  parentId={log.process_id}
                />
              ))}
            </Box>
          )}
        </Collapse>
      </Box>
    </Paper>
  );
};