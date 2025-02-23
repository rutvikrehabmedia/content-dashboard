import React, { useState, useEffect } from 'react';
import { Container, Paper, Typography, TextField, Button, Alert, Box, CircularProgress, Tabs, Tab, Chip } from '@mui/material';
import { Edit as EditIcon } from '@mui/icons-material';
import { ListManagementDialog } from './ListManagementDialog';
import { searchAPI } from '../services/api';

export const Settings: React.FC = () => {
  const [activeTab, setActiveTab] = useState(0);
  const [whitelist, setWhitelist] = useState<string[]>([]);
  const [blacklist, setBlacklist] = useState<string[]>([]);
  const [maxResults, setMaxResults] = useState(10);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [listDialogOpen, setListDialogOpen] = useState(false);

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

  const handleSave = async () => {
    try {
      setLoading(true);
      setError(null);
      
      await Promise.all([
        searchAPI.updateWhitelist(whitelist),
        searchAPI.updateBlacklist(blacklist),
        searchAPI.updateSettings({ maxResultsPerQuery: maxResults })
      ]);

      setSuccess('Settings saved successfully');
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      setError('Failed to save settings');
    } finally {
      setLoading(false);
    }
  };

  const handleRemoveUrl = (url: string, type: 'whitelist' | 'blacklist') => {
    if (type === 'whitelist') {
      setWhitelist(whitelist.filter((u) => u !== url));
    } else {
      setBlacklist(blacklist.filter((u) => u !== url));
    }
  };

  const handleSaveWhitelist = (newWhitelist: string[]) => {
    setWhitelist(newWhitelist);
  };

  const handleSaveBlacklist = (newBlacklist: string[]) => {
    setBlacklist(newBlacklist);
  };

  return (
    <Container maxWidth="xl">
      <Paper elevation={0} sx={{ p: 4, mb: 4, bgcolor: 'primary.main', color: 'white' }}>
        <Typography variant="h4" gutterBottom>
          Settings
        </Typography>
        <Typography variant="subtitle1">
          Manage global settings and filters
        </Typography>
      </Paper>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {success && (
        <Alert severity="success" sx={{ mb: 3 }}>
          {success}
        </Alert>
      )}

      <Paper sx={{ p: 3 }}>
        <Tabs value={activeTab} onChange={(_, newValue) => setActiveTab(newValue)} sx={{ mb: 3 }}>
          <Tab label="Search Settings" />
          <Tab label="Global Lists" />
        </Tabs>

        {activeTab === 0 ? (
          <Box>
            <Typography variant="h6" gutterBottom>
              Search Configuration
            </Typography>

            <TextField
              type="number"
              label="Maximum Results per Query"
              value={maxResults}
              onChange={(e) => setMaxResults(Number(e.target.value))}
              InputProps={{ inputProps: { min: 1, max: 100 } }}
              fullWidth
              sx={{ mb: 3 }}
            />

            <Button
              variant="contained"
              onClick={handleSave}
              disabled={loading}
            >
              {loading ? <CircularProgress size={24} /> : 'Save Settings'}
            </Button>
          </Box>
        ) : (
          <Box>
            <Typography variant="h6" gutterBottom>
              Global Lists Management
            </Typography>

            <Box sx={{ mb: 3 }}>
              <Typography variant="subtitle1" gutterBottom>
                Current Lists
              </Typography>
              
              <Box sx={{ mb: 2 }}>
                <Typography variant="subtitle2" color="primary">
                  Whitelist ({whitelist.length})
                </Typography>
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                  {whitelist.map((url, index) => (
                    <Chip
                      key={index}
                      label={url}
                      onDelete={() => handleRemoveUrl(url, 'whitelist')}
                      color="primary"
                      variant="outlined"
                    />
                  ))}
                </Box>
              </Box>

              <Box sx={{ mb: 2 }}>
                <Typography variant="subtitle2" color="error">
                  Blacklist ({blacklist.length})
                </Typography>
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                  {blacklist.map((url, index) => (
                    <Chip
                      key={index}
                      label={url}
                      onDelete={() => handleRemoveUrl(url, 'blacklist')}
                      color="error"
                      variant="outlined"
                    />
                  ))}
                </Box>
              </Box>

              <Button
                variant="outlined"
                onClick={() => setListDialogOpen(true)}
                startIcon={<EditIcon />}
              >
                Manage Lists
              </Button>
            </Box>
          </Box>
        )}
      </Paper>

      <ListManagementDialog
        open={listDialogOpen}
        onClose={() => setListDialogOpen(false)}
        whitelist={whitelist}
        blacklist={blacklist}
        onSaveWhitelist={handleSaveWhitelist}
        onSaveBlacklist={handleSaveBlacklist}
        isGlobal
      />
    </Container>
  );
}; 