import React, { useState, useEffect } from 'react';
import {
  Container,
  Paper,
  Typography,
  Box,
  Alert,
  Button,
  CircularProgress
} from '@mui/material';
import { ListManagementDialog } from './ListManagementDialog';
import { searchAPI } from '../services/api';
import DownloadIcon from '@mui/icons-material/Download';
import UploadIcon from '@mui/icons-material/Upload';

export const GlobalLists: React.FC = () => {
  const [whitelist, setWhitelist] = useState<string[]>([]);
  const [blacklist, setBlacklist] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);

  useEffect(() => {
    fetchLists();
  }, []);

  const fetchLists = async () => {
    try {
      setLoading(true);
      const [whitelistData, blacklistData] = await Promise.all([
        searchAPI.getWhitelist(),
        searchAPI.getBlacklist()
      ]);
      setWhitelist(whitelistData.urls);
      setBlacklist(blacklistData.urls);
    } catch (err) {
      setError('Failed to fetch lists');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async (newWhitelist: string[], newBlacklist: string[]) => {
    try {
      setLoading(true);
      setError(null);

      // Ensure arrays are initialized
      const currentWhitelist = whitelist || [];
      const currentBlacklist = blacklist || [];
      const updatedWhitelist = newWhitelist || [];
      const updatedBlacklist = newBlacklist || [];

      const updates: Promise<any>[] = [];

      // Only update if lists have changed
      if (!arraysEqual(updatedWhitelist, currentWhitelist)) {
        updates.push(searchAPI.updateWhitelist(updatedWhitelist));
      }
      if (!arraysEqual(updatedBlacklist, currentBlacklist)) {
        updates.push(searchAPI.updateBlacklist(updatedBlacklist));
      }

      if (updates.length > 0) {
        await Promise.all(updates);
        setWhitelist(updatedWhitelist);
        setBlacklist(updatedBlacklist);
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to update lists';
      setError(message);
      console.error('Error updating lists:', err);
    } finally {
      setLoading(false);
    }
  };

  // Helper function to compare arrays
  const arraysEqual = (a: string[], b: string[]) => {
    if (a.length !== b.length) return false;
    const sortedA = [...a].sort();
    const sortedB = [...b].sort();
    return sortedA.every((val, idx) => val === sortedB[idx]);
  };

  const downloadTemplate = () => {
    const template = {
      whitelist: [],
      blacklist: [],
      queries: [
        {
          query: "example query",
          whitelist: [],
          blacklist: []
        }
      ]
    };
    const blob = new Blob([JSON.stringify(template, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'bulk-search-template.json';
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <Container maxWidth="xl">
      <Paper elevation={0} sx={{ p: 4, mb: 4, bgcolor: 'primary.main', color: 'white' }}>
        <Typography variant="h4" gutterBottom>
          Global Lists Management
        </Typography>
        <Typography variant="subtitle1">
          Manage global whitelist and blacklist for all searches
        </Typography>
      </Paper>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      <Paper sx={{ p: 3, mb: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
          <Typography variant="h6">
            Current Lists
          </Typography>
          <Box sx={{ display: 'flex', gap: 2 }}>
            <Button
              startIcon={<DownloadIcon />}
              onClick={downloadTemplate}
              variant="outlined"
            >
              Download Template
            </Button>
            <Button
              variant="contained"
              onClick={() => setDialogOpen(true)}
              disabled={loading}
            >
              Manage Lists
            </Button>
          </Box>
        </Box>

        <Box sx={{ display: 'flex', gap: 4 }}>
          <Box flex={1}>
            <Typography variant="subtitle2" gutterBottom>
              Whitelist ({whitelist.length})
            </Typography>
            <Paper variant="outlined" sx={{ p: 2, minHeight: 100 }}>
              {whitelist.map((url, i) => (
                <Typography key={i} variant="body2">
                  {url}
                </Typography>
              ))}
            </Paper>
          </Box>
          <Box flex={1}>
            <Typography variant="subtitle2" gutterBottom>
              Blacklist ({blacklist.length})
            </Typography>
            <Paper variant="outlined" sx={{ p: 2, minHeight: 100 }}>
              {blacklist.map((url, i) => (
                <Typography key={i} variant="body2">
                  {url}
                </Typography>
              ))}
            </Paper>
          </Box>
        </Box>
      </Paper>

      <ListManagementDialog
        open={dialogOpen}
        onClose={() => setDialogOpen(false)}
        whitelist={whitelist}
        blacklist={blacklist}
        onSaveWhitelist={(w) => handleSave(w, blacklist)}
        onSaveBlacklist={(b) => handleSave(whitelist, b)}
        isGlobal={true}
      />
    </Container>
  );
}; 