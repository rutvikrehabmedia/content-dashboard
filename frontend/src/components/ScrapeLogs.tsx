import React, { useEffect, useState } from 'react';
import { searchAPI } from '../services/api';
import {
  Card,
  CardContent,
  Typography,
  Box,
  Chip,
  Collapse,
  IconButton,
  Pagination,
  CircularProgress,
  Grid,
  LinearProgress,
  Button,
  CardHeader,
  Paper,
  Menu,
  MenuItem,
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import { styled } from '@mui/material/styles';
import { formatDistance } from 'date-fns';
import { ContentViewer } from './ContentViewer';
import {
  Download as DownloadIcon,
  FilterList as FilterIcon,
  ContentCopy as ContentCopyIcon,
  FileDownload as FileDownloadIcon,
} from '@mui/icons-material';

const ExpandMore = styled((props: any) => {
  const { expand, ...other } = props;
  return <IconButton {...other} />;
})(({ theme, expand }) => ({
  transform: !expand ? 'rotate(0deg)' : 'rotate(180deg)',
  marginLeft: 'auto',
  transition: theme.transitions.create('transform', {
    duration: theme.transitions.duration.shortest,
  }),
}));

interface ScrapeLog {
  process_id: string;
  timestamp: string;
  status: string;
  type: string;
  url?: string;
  results?: Array<{
    url: string;
    title?: string;
    content?: string;
    error?: string;
    metadata?: {
      title?: string;
      description?: string;
      word_count?: number;
      language?: string;
      published_date?: string;
      author?: string;
      [key: string]: any;
    };
  }>;
  error?: string;
  metadata?: {
    total_urls?: number;
    completed?: number;
    failed?: number;
  };
}

const exportLog = (log: ScrapeLog, format: 'json' | 'csv') => {
  if (format === 'json') {
    const data = JSON.stringify(log, null, 2);
    const blob = new Blob([data], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `scrape-log-${log.process_id}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  } else {
    exportToCSV([log]); // Reuse the CSV export function
  }
};

const MetadataGrid: React.FC<{ metadata: Record<string, any> }> = ({ metadata }) => (
  <Grid container spacing={2}>
    {Object.entries(metadata).map(([key, value], index) => (
      <Grid item xs={4} key={index}>
        <Typography variant="body2">
          <strong>{key}:</strong> {value}
        </Typography>
      </Grid>
    ))}
  </Grid>
);

const ScrollableContent: React.FC<{ content: string }> = ({ content }) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
        <Typography variant="subtitle2">Content</Typography>
        <Button
          size="small"
          startIcon={<ContentCopyIcon />}
          onClick={handleCopy}
          sx={{ ml: 2 }}
        >
          {copied ? 'Copied!' : 'Copy'}
        </Button>
      </Box>
      <Paper
        variant="outlined"
        sx={{
          p: 2,
          maxHeight: '300px',
          overflow: 'auto',
          bgcolor: 'grey.50',
          fontFamily: 'monospace',
          whiteSpace: 'pre-wrap',
          wordBreak: 'break-word',
        }}
      >
        {content}
      </Paper>
    </Box>
  );
};

const getStatusColor = (status: string): 'success' | 'warning' | 'info' | 'error' | 'default' => {
  switch (status.toLowerCase()) {
    case 'completed':
      return 'success';
    case 'processing':
      return 'warning';
    case 'started':
      return 'info';
    case 'error':
    case 'failed':
      return 'error';
    default:
      return 'default';
  }
};

const ResultCard: React.FC<{ result: ScrapeLog['results'][number] }> = ({ result }) => {
  const [expanded, setExpanded] = useState(false);

  return (
    <Card variant="outlined" sx={{ mb: 2 }}>
      <CardHeader
        title={
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <Typography variant="subtitle1" sx={{ flexGrow: 1 }}>
              {result.url}
            </Typography>
            <IconButton
              onClick={() => setExpanded(!expanded)}
              sx={{
                transform: expanded ? 'rotate(180deg)' : 'none',
                transition: 'transform 0.2s',
              }}
            >
              <ExpandMoreIcon />
            </IconButton>
          </Box>
        }
      />
      <Collapse in={expanded}>
        <CardContent>
          {result.content && (
            <Box sx={{ mb: 3 }}>
              <ScrollableContent content={result.content} />
            </Box>
          )}
          {result.metadata && (
            <Box>
              <Typography variant="subtitle2" gutterBottom>
                Metadata
              </Typography>
              <MetadataGrid metadata={result.metadata} />
            </Box>
          )}
        </CardContent>
      </Collapse>
    </Card>
  );
};

const ScrapeLogCard: React.FC<{ log: ScrapeLog }> = ({ log }) => {
  const [expanded, setExpanded] = useState(false);
  const isBulkScrape = log.metadata?.total_urls && log.metadata.total_urls > 1;
  const [exportAnchorEl, setExportAnchorEl] = useState<null | HTMLElement>(null);

  const handleExportClick = (event: React.MouseEvent<HTMLElement>) => {
    event.stopPropagation();
    setExportAnchorEl(event.currentTarget);
  };

  const handleExportClose = () => {
    setExportAnchorEl(null);
  };

  return (
    <Card>
      <CardHeader
        title={
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <Typography variant="h6" sx={{ flexGrow: 1 }}>
              {isBulkScrape ? 'Bulk Scrape' : log.url}
              <Chip
                label={log.status}
                color={getStatusColor(log.status)}
                size="small"
                sx={{ ml: 2 }}
              />
              {isBulkScrape && (
                <Chip
                  label={`${log.results?.length || 0} results`}
                  size="small"
                  sx={{ ml: 1 }}
                />
              )}
            </Typography>
            <Box>
              <IconButton onClick={handleExportClick} title="Export log">
                <DownloadIcon />
              </IconButton>
              <Menu
                anchorEl={exportAnchorEl}
                open={Boolean(exportAnchorEl)}
                onClose={handleExportClose}
              >
                <MenuItem onClick={() => { exportLog(log, 'json'); handleExportClose(); }}>
                  Export as JSON
                </MenuItem>
                <MenuItem onClick={() => { exportLog(log, 'csv'); handleExportClose(); }}>
                  Export as CSV
                </MenuItem>
              </Menu>
            </Box>
          </Box>
        }
        subheader={
          <Box>
            <Typography variant="caption" display="block">
              ID: {log.process_id}
            </Typography>
            <Typography variant="caption" display="block">
              {new Date(log.timestamp).toLocaleString()}
            </Typography>
          </Box>
        }
        action={
          <Box>
            <IconButton
              onClick={() => setExpanded(!expanded)}
              sx={{
                transform: expanded ? 'rotate(180deg)' : 'none',
                transition: 'transform 0.2s',
              }}
            >
              <ExpandMoreIcon />
            </IconButton>
          </Box>
        }
      />

      <Collapse in={expanded}>
        <CardContent>
          {isBulkScrape ? (
            // Bulk scrape results
            <Box>
              {log.results?.map((result, index) => (
                <ResultCard key={index} result={result} />
              ))}
            </Box>
          ) : (
            // Single scrape result
            log.results?.[0] && (
              <>
                {log.results[0].content && (
                  <Box sx={{ mb: 3 }}>
                    <ScrollableContent content={log.results[0].content} />
                  </Box>
                )}
                {log.results[0].metadata && (
                  <Box>
                    <Typography variant="subtitle2" gutterBottom>
                      Metadata
                    </Typography>
                    <MetadataGrid metadata={log.results[0].metadata} />
                  </Box>
                )}
              </>
            )
          )}
        </CardContent>
      </Collapse>
    </Card>
  );
};

const exportToCSV = (logs: ScrapeLog[]) => {
  const headers = [
    'Process ID',
    'Timestamp',
    'Status',
    'Type',
    'URL',
    'Title',
    'Content',
    'Error',
    'Metadata',
  ];

  const rows = logs.flatMap(log => {
    if (log.results && log.results.length > 0) {
      return log.results.map(result => [
        log.process_id,
        new Date(log.timestamp).toLocaleString(),
        log.status,
        log.type,
        result.url,
        result.title || '',
        result.content || '',
        result.error || '',
        result.metadata ? JSON.stringify(result.metadata) : '',
      ]);
    }
    return [[
      log.process_id,
      new Date(log.timestamp).toLocaleString(),
      log.status,
      log.type,
      log.url || '',
      '',
      '',
      log.error || '',
      log.metadata ? JSON.stringify(log.metadata) : '',
    ]];
  });

  const csvContent = [
    headers.join(','),
    ...rows.map(row => row.map(cell => 
      typeof cell === 'string' ? `"${cell.replace(/"/g, '""')}"` : cell
    ).join(','))
  ].join('\n');

  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = `scrape-logs-${new Date().toISOString()}.csv`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
};

export const ScrapeLogs: React.FC = () => {
  const [logs, setLogs] = useState<ScrapeLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);

  const fetchLogs = async () => {
    try {
      setLoading(true);
      const response = await searchAPI.getScrapeLogs(page);
      setLogs(response.logs);
      setTotalPages(Math.ceil(response.total / response.per_page));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch logs');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
    // Set up polling for active processes
    const interval = setInterval(fetchLogs, 5000);
    return () => clearInterval(interval);
  }, [page]);

  if (loading && !logs.length) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
        <Typography variant="h5" sx={{ flexGrow: 1 }}>
          Scrape Logs
        </Typography>
      </Box>

      {error && (
        <Typography color="error" sx={{ mb: 2 }}>
          {error}
        </Typography>
      )}

      <Grid container spacing={2}>
        {logs.map((log) => (
          <Grid item xs={12} key={log.process_id}>
            <ScrapeLogCard log={log} />
          </Grid>
        ))}
      </Grid>

      <Box sx={{ mt: 2, display: 'flex', justifyContent: 'center' }}>
        <Pagination
          count={totalPages}
          page={page}
          onChange={(_, value) => setPage(value)}
        />
      </Box>
    </Box>
  );
}; 