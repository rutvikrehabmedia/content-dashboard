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
  OpenInNew as OpenInNewIcon,
} from '@mui/icons-material';
import { SearchResultCard } from './SearchResultCard';
import { exportToCSV, exportToJSON } from '../utils/exportUtils';
import { LogEntry } from '../services/api';

// Define types
interface LogCardProps {
  log: LogEntry;
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
  const [expandedResults, setExpandedResults] = useState<Record<string, boolean>>({});
  const [exportMenu, setExportMenu] = useState<null | HTMLElement>(null);

  const handleExportClick = (event: React.MouseEvent<HTMLElement>) => {
    setExportMenu(event.currentTarget);
  };

  const handleExport = (format: 'csv' | 'json') => {
    setExportMenu(null);
    const exportData: Partial<LogEntry> = {
      process_id: log.process_id,
      query: log.query,
      status: log.status,
      timestamp: log.timestamp,
      results: log.results || [],
      error: log.error,
      metadata: log.metadata,
      child_logs: log.child_logs
    };
    
    if (format === 'csv') {
      exportToCSV(exportData);
    } else {
      exportToJSON(exportData);
    }
  };

  const handleCopy = (content: string) => {
    navigator.clipboard.writeText(content);
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

  const toggleResultExpand = (resultId: string) => {
    setExpandedResults(prev => ({
      ...prev,
      [resultId]: !prev[resultId]
    }));
  };

  const renderChildLogs = () => {
    if (!log.child_logs?.length) return null;

    return (
      <Box sx={{ mt: 2 }}>
        <Typography variant="subtitle1" gutterBottom>
          Individual Queries
        </Typography>
        {log.child_logs.map((childLog) => (
          <Paper 
            key={childLog.process_id} 
            elevation={1} 
            sx={{ 
              p: 2, 
              mb: 2,
              bgcolor: 'background.paper',
              '&:hover': {
                bgcolor: 'action.hover'
              }
            }}
          >
            <Grid container justifyContent="space-between" alignItems="flex-start">
              <Grid item xs>
                <Typography variant="subtitle1" gutterBottom>
                  {childLog.query}
                </Typography>
                <Box sx={{ display: 'flex', gap: 1, mb: 1 }}>
                  <Chip
                    label={childLog.status}
                    color={getStatusChipColor(childLog.status)}
                    size="small"
                  />
                  {childLog.results && (
                    <Chip
                      label={`${childLog.results.length} results`}
                      color="primary"
                      size="small"
                    />
                  )}
                </Box>
                <Typography variant="body2" color="text.secondary">
                  ID: {childLog.process_id}
                  <IconButton size="small" onClick={() => navigator.clipboard.writeText(childLog.process_id)}>
                    <CopyIcon fontSize="small" />
                  </IconButton>
                </Typography>
              </Grid>
            </Grid>

            {childLog.results && childLog.results.length > 0 && (
              <Box sx={{ mt: 2 }}>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Results:
                </Typography>
                <Box sx={{ maxHeight: '300px', overflowY: 'auto' }}>
                  {childLog.results.map((result, index) => (
                    <Paper
                      key={`${result.url}-${index}`}
                      elevation={1}
                      sx={{
                        p: 2,
                        mb: 1,
                        bgcolor: 'background.default',
                        '&:hover': {
                          bgcolor: 'action.hover'
                        }
                      }}
                    >
                      <Grid container justifyContent="space-between" alignItems="flex-start">
                        <Grid item xs>
                          <Typography variant="subtitle2" gutterBottom>
                            {result.title || result.url}
                          </Typography>
                          <Typography variant="body2" color="text.secondary" gutterBottom>
                            {result.url}
                          </Typography>
                          <Box sx={{ display: 'flex', gap: 1, mt: 1 }}>
                            {result.score !== undefined && (
                              <Chip 
                                label={`Score: ${result.score.toFixed(2)}`}
                                size="small"
                                color={result.score > 0.5 ? "success" : "default"}
                              />
                            )}
                          </Box>
                        </Grid>

                        <Grid item>
                          <Box sx={{ display: 'flex', gap: 1 }}>
                            <IconButton 
                              size="small"
                              onClick={() => handleCopy(result.content || result.url)}
                              title="Copy Content"
                            >
                              <CopyIcon fontSize="small" />
                            </IconButton>
                            <IconButton
                              size="small"
                              component="a"
                              href={result.url}
                              target="_blank"
                              title="Open in new tab"
                            >
                              <OpenInNewIcon fontSize="small" />
                            </IconButton>
                            <IconButton
                              size="small"
                              onClick={() => toggleResultExpand(`${childLog.process_id}-${index}`)}
                              title={expandedResults[`${childLog.process_id}-${index}`] ? "Show less" : "Show more"}
                            >
                              {expandedResults[`${childLog.process_id}-${index}`] ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                            </IconButton>
                          </Box>
                        </Grid>
                      </Grid>

                      <Collapse in={expandedResults[`${childLog.process_id}-${index}`]}>
                        <Divider sx={{ my: 2 }} />

                        {result.content && (
                          <Box sx={{ mt: 2 }}>
                            <Typography variant="body2" color="text.secondary">
                              Content Preview:
                            </Typography>
                            <Box 
                              sx={{ 
                                mt: 1,
                                maxHeight: '200px',
                                overflowY: 'auto',
                                bgcolor: 'background.paper',
                                p: 2,
                                borderRadius: 1,
                                border: '1px solid',
                                borderColor: 'divider'
                              }}
                            >
                              <Typography variant="body2" component="pre" sx={{ whiteSpace: 'pre-wrap' }}>
                                {result.content}
                              </Typography>
                            </Box>
                          </Box>
                        )}

                        {result.metadata && Object.keys(result.metadata).length > 0 && (
                          <Box sx={{ mt: 2 }}>
                            <Typography variant="body2" color="text.secondary" gutterBottom>
                              Metadata:
                            </Typography>
                            <Grid container spacing={2} sx={{ mt: 1 }}>
                              {Object.entries(result.metadata).map(([key, value]) => (
                                <Grid item xs={12} sm={4} key={key}>
                                  <Box sx={{ 
                                    p: 1, 
                                    bgcolor: 'background.default',
                                    borderRadius: 1,
                                    height: '100%'
                                  }}>
                                    <Typography variant="body2" component="span" fontWeight="bold">
                                      {key}:
                                    </Typography>
                                    <Typography variant="body2" component="span" sx={{ ml: 1 }}>
                                      {String(value)}
                                    </Typography>
                                  </Box>
                                </Grid>
                              ))}
                            </Grid>
                          </Box>
                        )}
                      </Collapse>
                    </Paper>
                  ))}
                </Box>
              </Box>
            )}

            {childLog.error && (
              <Typography color="error" variant="body2" sx={{ mt: 1 }}>
                Error: {childLog.error}
              </Typography>
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
              {log.status === 'completed' && log.results && (
                <Chip
                  label={`${log.results.length} results`}
                  color="primary"
                  size="small"
                  sx={{ ml: 1 }}
                />
              )}
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