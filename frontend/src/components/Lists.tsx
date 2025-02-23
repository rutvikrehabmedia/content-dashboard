import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Tabs,
  Tab,
  TextField,
  Button,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Typography,
  Alert,
} from '@mui/material';
import DeleteIcon from '@mui/icons-material/Delete';
import { searchAPI } from '../services/api';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

export const Lists: React.FC = () => {
  const [tabValue, setTabValue] = useState(0);
  const [newUrl, setNewUrl] = useState('');
  const [whitelist, setWhitelist] = useState<string[]>([]);
  const [blacklist, setBlacklist] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const fetchLists = async () => {
    try {
      const [whitelistResponse, blacklistResponse] = await Promise.all([
        searchAPI.getWhitelist(),
        searchAPI.getBlacklist()
      ]);
      setWhitelist(whitelistResponse.urls);
      setBlacklist(blacklistResponse.urls);
    } catch (err) {
      setError('Failed to fetch lists');
    }
  };

  useEffect(() => {
    fetchLists();
  }, []);

  const handleAddUrl = async () => {
    try {
      setError(null);
      setSuccess(null);
      
      if (!newUrl.trim()) {
        setError('Please enter a URL');
        return;
      }

      const isWhitelist = tabValue === 0;
      const response = await (isWhitelist 
        ? searchAPI.updateWhitelist([...whitelist, newUrl])
        : searchAPI.updateBlacklist([...blacklist, newUrl]));

      if (response.success) {
        setSuccess(`URL added to ${isWhitelist ? 'whitelist' : 'blacklist'}`);
        setNewUrl('');
        fetchLists();
      }
    } catch (err) {
      setError('Failed to add URL');
    }
  };

  const handleRemoveUrl = async (url: string) => {
    try {
      const isWhitelist = tabValue === 0;
      const currentList = isWhitelist ? whitelist : blacklist;
      const updatedList = currentList.filter(item => item !== url);
      
      await (isWhitelist 
        ? searchAPI.updateWhitelist(updatedList)
        : searchAPI.updateBlacklist(updatedList));
      
      fetchLists();
    } catch (err) {
      setError('Failed to remove URL');
    }
  };

  return (
    <Box sx={{ width: '100%' }}>
      <Paper sx={{ width: '100%', mb: 2 }}>
        <Tabs
          value={tabValue}
          onChange={(_, newValue) => setTabValue(newValue)}
          indicatorColor="primary"
          textColor="primary"
        >
          <Tab label="Whitelist" />
          <Tab label="Blacklist" />
        </Tabs>
      </Paper>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {success && (
        <Alert severity="success" sx={{ mb: 2 }}>
          {success}
        </Alert>
      )}

      <Box sx={{ mb: 3 }}>
        <TextField
          fullWidth
          label="Add URL"
          value={newUrl}
          onChange={(e) => setNewUrl(e.target.value)}
          sx={{ mb: 1 }}
        />
        <Button
          variant="contained"
          onClick={handleAddUrl}
          disabled={!newUrl.trim()}
        >
          Add to {tabValue === 0 ? 'Whitelist' : 'Blacklist'}
        </Button>
      </Box>

      <TabPanel value={tabValue} index={0}>
        <List>
          {whitelist.map((url) => (
            <ListItem key={url}>
              <ListItemText primary={url} />
              <ListItemSecondaryAction>
                <IconButton edge="end" onClick={() => handleRemoveUrl(url)}>
                  <DeleteIcon />
                </IconButton>
              </ListItemSecondaryAction>
            </ListItem>
          ))}
        </List>
      </TabPanel>

      <TabPanel value={tabValue} index={1}>
        <List>
          {blacklist.map((url) => (
            <ListItem key={url}>
              <ListItemText primary={url} />
              <ListItemSecondaryAction>
                <IconButton edge="end" onClick={() => handleRemoveUrl(url)}>
                  <DeleteIcon />
                </IconButton>
              </ListItemSecondaryAction>
            </ListItem>
          ))}
        </List>
      </TabPanel>
    </Box>
  );
}; 