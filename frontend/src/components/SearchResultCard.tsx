import React, { useState } from 'react';
import {
  Box,
  Typography,
  Paper,
  Grid,
  IconButton,
  Tooltip,
  Snackbar,
  Collapse,
} from '@mui/material';
import {
  ContentCopy as CopyIcon,
  OpenInNew as OpenInNewIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
} from '@mui/icons-material';
import { RelevanceScore } from './RelevanceScore';
import { SearchResult } from '../services/api';

interface SearchResultCardProps {
  result: SearchResult;
  index: number;
  parentId?: string;
}

export const SearchResultCard: React.FC<SearchResultCardProps> = ({
  result,
  index,
  parentId = 'search',
}) => {
  const [copySuccess, setCopySuccess] = useState(false);
  const [expanded, setExpanded] = useState(false);

  const handleCopyContent = (content: string | undefined) => {
    if (!content) return;
    navigator.clipboard.writeText(content);
    setCopySuccess(true);
  };

  const toggleExpand = () => {
    setExpanded((prev) => !prev);
  };

  if (!result) return null;

  const url = typeof result.url === 'object' ? result.url.url : result.url;
  const title = typeof result.url === 'object'
    ? result.url.title
    : (result.title || url);
  const content = typeof result.url === 'object'
    ? result.url.content
    : result.content;
  const score = typeof result.url === 'object'
    ? result.url.score || 0
    : (result.score || 0);
  const metadata = typeof result.url === 'object'
    ? result.url.metadata
    : result.metadata;

  return (
    <Paper key={`${parentId}-result-${index}`} sx={{ p: 2, mb: 2 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
        <Box sx={{ flex: 1 }}>
          <Typography
            component="a"
            href={url}
            target="_blank"
            rel="noopener noreferrer"
            sx={{ textDecoration: 'none', color: 'primary.main', display: 'block' }}
          >
            {title}
          </Typography>
          <Typography variant="caption" color="text.secondary">
            {url}
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <RelevanceScore score={score} />
          <Tooltip title="Copy content">
            <span>
              <IconButton
                size="small"
                onClick={() => handleCopyContent(content)}
                disabled={!content}
              >
                <CopyIcon />
              </IconButton>
            </span>
          </Tooltip>
          <Tooltip title="Open in new tab">
            <IconButton size="small" href={url} target="_blank">
              <OpenInNewIcon />
            </IconButton>
          </Tooltip>
          <IconButton size="small" onClick={toggleExpand}>
            {expanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
          </IconButton>
        </Box>
      </Box>

      <Collapse in={expanded}>
        <Box sx={{ 
          mt: 1, 
          maxHeight: '200px', 
          overflowY: 'auto', 
          bgcolor: 'grey.50', 
          p: 1, 
          borderRadius: 1 
        }}>
          <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
            {content || 'No content available'}
          </Typography>
        </Box>

        {metadata && Object.keys(metadata).length > 0 && (
          <Box sx={{ mt: 2 }}>
            <Typography variant="caption" color="text.secondary" gutterBottom>
              Metadata
            </Typography>
            <Grid container spacing={2}>
              {Object.entries(metadata).map(([key, value], i) => (
                <Grid item xs={12} sm={4} key={`${parentId}-metadata-${i}`}>
                  <Typography variant="caption" display="block">
                    <strong>{key}:</strong>{' '}
                    {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                  </Typography>
                </Grid>
              ))}
            </Grid>
          </Box>
        )}
      </Collapse>

      <Snackbar
        open={copySuccess}
        autoHideDuration={2000}
        onClose={() => setCopySuccess(false)}
        message="Content copied to clipboard"
      />
    </Paper>
  );
}; 