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
import { BulkSearchLog, LogEntry } from '../services/api';
import { SearchResults } from './SearchResults';
import { BulkSearchResults } from './BulkSearchResults';
import { getStatusChipColor, getStatusText, StatusType } from '../utils/statusUtils';
import { exportToCSV, exportToJSON } from '../utils/exportUtils';
import { SearchResultCard } from './SearchResultCard';

// Helper to determine the query type for display
const getSearchType = (log: LogEntry) => {
  if (log.query.includes('\n')) {
    return 'Bulk Query Search';
  }
  if (log.urls && Array.isArray(log.urls)) {
    return 'Bulk Scraper';
  }
  if (log.url) {
    return 'Single Scraper';
  }
  return 'Single Query Search';
};

interface LogCardProps {
  log: BulkSearchLog;
  onRefresh: () => void;
}

export const LogCard: React.FC<LogCardProps> = ({ log, onRefresh }) => {
  const [expanded, setExpanded] = useState(false);
  const [exportMenu, setExportMenu] = useState<null | HTMLElement>(null);
  const [showMetadata, setShowMetadata] = useState(false);

  const handleCopyId = () => {
    navigator.clipboard.writeText(log.process_id);
  };

  const handleExportClick = (event: React.MouseEvent<HTMLElement>) => {
    setExportMenu(event.currentTarget);
  };

  const handleExportClose = () => {
    setExportMenu(null);
  };

  const handleExport = (format: 'csv' | 'json') => {
    handleExportClose();
    if (format === 'csv') {
      exportToCSV(log);
    } else {
      exportToJSON(log);
    }
  };

  const renderMetadataSection = () => {
    if (!log.metadata) return null;

    // Split metadata into two groups for demonstration purposes.
    const metaGroups = {
      status: {
        title: 'Status Info',
        fields: ['total_queries', 'completed_queries', 'successful_queries']
      },
      settings: {
        title: 'Settings',
        fields: ['global_lists_enabled']
      }
    };

    return (
      <Grid container spacing={3}>
        {Object.entries(metaGroups).map(([group, { title, fields }]) => (
          <Grid item xs={12} md={6} key={group}>
            <Typography variant="subtitle2" gutterBottom>{title}</Typography>
            {fields.map(field => (
              <Typography key={field} variant="body2" color="textSecondary">
                {field
                  .split('_')
                  .map(w => w.charAt(0).toUpperCase() + w.slice(1))
                  .join(' ')}
                :{' '}
                {typeof log.metadata![field] === 'boolean'
                  ? log.metadata![field]
                    ? 'Yes'
                    : 'No'
                  : log.metadata![field]}
              </Typography>
            ))}
          </Grid>
        ))}
      </Grid>
    );
  };

  const renderProgress = () => {
    if (!log.progress) return null;
    const { total, completed, failed } = log.progress;
    const percentage = Math.round((completed / total) * 100);

    return (
      <Box sx={{ mt: 2, mb: 1 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
          <Typography variant="body2">Progress: {percentage}%</Typography>
          <Typography variant="body2">
            {completed} of {total} completed {failed > 0 && `(${failed} failed)`}
          </Typography>
        </Box>
        <LinearProgress
          variant="determinate"
          value={percentage}
          color={failed > 0 ? 'warning' : 'primary'}
        />
      </Box>
    );
  };

  return (
    <Paper
      elevation={1}
      sx={{
        mb: 2,
        borderLeft: 6,
        borderColor: getStatusChipColor(log.status as StatusType)
      }}
    >
      <Box sx={{ p: 2 }}>
        <Grid container alignItems="center" spacing={2}>
          <Grid item xs>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Typography variant="h6">
                {log.query === 'BULK_SEARCH' ? 'Bulk Search' : log.query}
              </Typography>
              <Chip
                label={getStatusText(log.status as StatusType)}
                color={getStatusChipColor(log.status as StatusType)}
                size="small"
              />
              {log.results && (
                <Chip
                  label={
                    log.query === 'BULK_SEARCH'
                      ? `${log.results.length} results`
                      : log.results.length > 0
                        ? "No of Results: " + log.results.length
                        : "No result"
                  }
                  size="small"
                  color='primary'
                  variant="outlined"
                />
              )}
              <Chip
                label={getSearchType(log)}
                size="small"
                variant="outlined"
              />
            </Box>
            <Typography variant="caption" display="block" sx={{ mt: 0.5 }}>
              ID: {log.process_id}
              <IconButton size="small" onClick={handleCopyId}>
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
          onClose={handleExportClose}
        >
          <MenuItem onClick={() => handleExport('csv')}>Export as CSV</MenuItem>
          <MenuItem onClick={() => handleExport('json')}>Export as JSON</MenuItem>
        </Menu>

        <Collapse in={expanded}>
          <Divider sx={{ my: 2 }} />

          <Collapse in={showMetadata}>
            <Box sx={{ mt: 2, mb: 2 }}>
              {renderMetadataSection()}
            </Box>
          </Collapse>

          <Box sx={{ mt: 2 }}>
            {log.query === 'BULK_SEARCH' ? (
              <BulkSearchResults log={log} />
            ) : (
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
          </Box>
        </Collapse>
      </Box>
    </Paper>
  );
}; 