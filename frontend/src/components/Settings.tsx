import React, { useState, useEffect } from 'react';
import { 
  Container, Paper, Typography, TextField, Button, Alert, 
  Box, Grid, Card, CardContent, Tabs, Tab, Chip 
} from '@mui/material';
import { Edit as EditIcon } from '@mui/icons-material';
import { ListManagementDialog } from './ListManagementDialog';
import { searchAPI } from '../services/api';

export const Settings: React.FC = () => {
  const [activeTab, setActiveTab] = useState(0);
  const [whitelist, setWhitelist] = useState<string[]>([]);
  const [blacklist, setBlacklist] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [listDialogOpen, setListDialogOpen] = useState(false);
  const [settings, setSettings] = useState({
    maxResultsPerQuery: 10,
    searchResultsLimit: 2,
    scrapeLimit: 2,
    minScoreThreshold: 0.2,
    jinaRateLimit: 20,
    searchRateLimit: 20,
  });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [settingsData, whitelistData, blacklistData] = await Promise.all([
        searchAPI.getSettings(),
        searchAPI.getWhitelist(),
        searchAPI.getBlacklist()
      ]);
      setSettings(settingsData);
      setWhitelist(whitelistData.urls);
      setBlacklist(blacklistData.urls);
    } catch (err) {
      setError('Failed to fetch data');
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

  const handleSave = async () => {
    try {
      setLoading(true);
      setError(null);
      
      await Promise.all([
        searchAPI.updateSettings(settings),
        searchAPI.updateWhitelist(whitelist),
        searchAPI.updateBlacklist(blacklist)
      ]);

      setSuccess('Settings updated successfully');
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      setError('Failed to update settings');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container maxWidth="xl">
      <Paper elevation={0} sx={{ p: 4, mb: 4, bgcolor: 'primary.main', color: 'white' }}>
        <Typography variant="h4" gutterBottom>
          Settings
        </Typography>
        <Typography variant="subtitle1">
          Configure search and scraping parameters
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
          <Card>
            <CardContent>
              <Grid container spacing={3}>
                <Grid item xs={12}>
                  <Typography variant="h6" gutterBottom>Search Settings</Typography>
                </Grid>
                
                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    label="Max Results Per Query"
                    type="number"
                    value={settings.maxResultsPerQuery}
                    onChange={(e) => setSettings({
                      ...settings,
                      maxResultsPerQuery: parseInt(e.target.value)
                    })}
                    helperText="Maximum number of results to return per search query"
                  />
                </Grid>

                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    label="Search Results Limit"
                    type="number"
                    value={settings.searchResultsLimit}
                    onChange={(e) => setSettings({
                      ...settings,
                      searchResultsLimit: parseInt(e.target.value)
                    })}
                    helperText="Number of top results to display"
                  />
                </Grid>

                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    label="Scrape Limit"
                    type="number"
                    value={settings.scrapeLimit}
                    onChange={(e) => setSettings({
                      ...settings,
                      scrapeLimit: parseInt(e.target.value)
                    })}
                    helperText="Maximum number of URLs to scrape content from"
                  />
                </Grid>

                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    label="Minimum Score Threshold"
                    type="number"
                    inputProps={{ step: 0.1, min: 0, max: 1 }}
                    value={settings.minScoreThreshold}
                    onChange={(e) => setSettings({
                      ...settings,
                      minScoreThreshold: parseFloat(e.target.value)
                    })}
                    helperText="Minimum relevance score for results (0-1)"
                  />
                </Grid>

                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    label="Jina Rate Limit"
                    type="number"
                    value={settings.jinaRateLimit}
                    onChange={(e) => setSettings({
                      ...settings,
                      jinaRateLimit: parseInt(e.target.value)
                    })}
                    helperText="Maximum Jina API requests per minute"
                  />
                </Grid>

                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    label="Search Rate Limit"
                    type="number"
                    value={settings.searchRateLimit}
                    onChange={(e) => setSettings({
                      ...settings,
                      searchRateLimit: parseInt(e.target.value)
                    })}
                    helperText="Maximum search requests per minute"
                  />
                </Grid>

                <Grid item xs={12}>
                  <Button 
                    variant="contained" 
                    color="primary" 
                    onClick={handleSave}
                    disabled={loading}
                  >
                    {loading ? 'Saving...' : 'Save Settings'}
                  </Button>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
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