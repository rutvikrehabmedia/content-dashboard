import React, { useState } from 'react';
import {
  Box,
  Typography,
  IconButton,
  Collapse,
  Button,
  Snackbar,
  Paper,
} from '@mui/material';
import {
  ContentCopy as CopyIcon,
  ExpandMore as ExpandMoreIcon,
} from '@mui/icons-material';
import { styled } from '@mui/material/styles';

const ExpandButton = styled(IconButton)(({ theme, expanded }: { theme: any, expanded: boolean }) => ({
  transform: expanded ? 'rotate(180deg)' : 'rotate(0deg)',
  transition: theme.transitions.create('transform', {
    duration: theme.transitions.duration.shortest,
  }),
}));

interface ContentViewerProps {
  content: string;
  maxHeight?: number;
  label?: string;
}

export const ContentViewer: React.FC<ContentViewerProps> = ({
  content,
  maxHeight = 200,
  label = 'Content',
}) => {
  const [expanded, setExpanded] = useState(false);
  const [showCopyNotification, setShowCopyNotification] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(content);
    setShowCopyNotification(true);
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
        <Typography variant="body2" color="text.secondary">
          {label}
        </Typography>
        <IconButton size="small" onClick={handleCopy} sx={{ ml: 1 }}>
          <CopyIcon fontSize="small" />
        </IconButton>
        <ExpandButton
          size="small"
          onClick={() => setExpanded(!expanded)}
          expanded={expanded}
          sx={{ ml: 'auto' }}
        >
          <ExpandMoreIcon fontSize="small" />
        </ExpandButton>
      </Box>

      <Collapse in={expanded} timeout="auto">
        <Paper
          variant="outlined"
          sx={{
            p: 1,
            maxHeight: maxHeight,
            overflow: 'auto',
            bgcolor: 'grey.50',
          }}
        >
          <Typography
            variant="body2"
            component="pre"
            sx={{
              whiteSpace: 'pre-wrap',
              wordBreak: 'break-word',
              fontFamily: 'monospace',
            }}
          >
            {content}
          </Typography>
        </Paper>
      </Collapse>

      <Snackbar
        open={showCopyNotification}
        autoHideDuration={2000}
        onClose={() => setShowCopyNotification(false)}
        message="Content copied to clipboard"
      />
    </Box>
  );
}; 