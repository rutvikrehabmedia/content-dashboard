import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  Box,
  Chip,
  Tabs,
  Tab,
  Typography,
  Alert,
  CircularProgress
} from '@mui/material';
import { searchAPI } from '../services/api';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

const TabPanel: React.FC<TabPanelProps> = ({ children, value, index }) => (
  <div role="tabpanel" hidden={value !== index}>
    {value === index && <Box sx={{ py: 2 }}>{children}</Box>}
  </div>
);

interface ListManagementDialogProps {
  open: boolean;
  onClose: () => void;
  whitelist: string[];
  blacklist: string[];
  onSaveWhitelist: (whitelist: string[]) => void;
  onSaveBlacklist: (blacklist: string[]) => void;
  isGlobal?: boolean;
}

export const ListManagementDialog: React.FC<ListManagementDialogProps> = ({
  open,
  onClose,
  whitelist,
  blacklist,
  onSaveWhitelist,
  onSaveBlacklist,
  isGlobal = false
}) => {
  const [tabValue, setTabValue] = useState(0);
  const [newUrl, setNewUrl] = useState('');
  const [localWhitelist, setLocalWhitelist] = useState([...whitelist]);
  const [localBlacklist, setLocalBlacklist] = useState([...blacklist]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLocalWhitelist([...whitelist]);
    setLocalBlacklist([...blacklist]);
  }, [whitelist, blacklist]);

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
    setNewUrl('');
  };

  const handleSave = async () => {
    try {
      setLoading(true);
      setError(null);

      // Ensure we have arrays
      const whitelist = localWhitelist || [];
      const blacklist = localBlacklist || [];

      if (isGlobal) {
        const updates: Promise<any>[] = [];
        
        // Always send updates for global lists
        updates.push(searchAPI.updateWhitelist(whitelist));
        updates.push(searchAPI.updateBlacklist(blacklist));

        await Promise.all(updates);
      }

      // Update local state
      onSaveWhitelist(whitelist);
      onSaveBlacklist(blacklist);
      onClose();
    } catch (err) {
      console.error('Error saving lists:', err);
      setError(err instanceof Error ? err.message : 'Failed to save lists. Please try again.');
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

  // Validate URL format
  const isValidUrl = (url: string): boolean => {
    try {
      new URL(url);
      return true;
    } catch {
      return false;
    }
  };

  // Validate list of URLs
  const isValidList = (list: string[]): boolean => {
    return Array.isArray(list) && list.every(url => !url || isValidUrl(url));
  };

  const handleAdd = () => {
    if (!newUrl) return;

    try {
      // Basic URL validation
      let urlToAdd = newUrl;
      
      // Add protocol if missing
      if (!urlToAdd.startsWith('http://') && !urlToAdd.startsWith('https://')) {
        urlToAdd = 'https://' + urlToAdd;
      }

      // Validate URL format
      new URL(urlToAdd);

      if (tabValue === 0) { // Whitelist
        if (!localWhitelist.includes(urlToAdd)) {
          setLocalWhitelist(prev => [...prev, urlToAdd]);
        } else {
          setError('URL already exists in whitelist');
          return;
        }
      } else { // Blacklist
        if (!localBlacklist.includes(urlToAdd)) {
          setLocalBlacklist(prev => [...prev, urlToAdd]);
        } else {
          setError('URL already exists in blacklist');
          return;
        }
      }
      
      setNewUrl('');
      setError(null);
    } catch (err) {
      setError('Please enter a valid URL');
    }
  };

  const handleKeyPress = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      handleAdd();
    }
  };

  const handleRemove = (url: string) => {
    if (tabValue === 0) {
      setLocalWhitelist(prev => prev.filter(u => u !== url));
    } else {
      setLocalBlacklist(prev => prev.filter(u => u !== url));
    }
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>
        {isGlobal ? 'Manage Global Lists' : 'Manage Custom Lists'}
      </DialogTitle>
      <DialogContent>
        <Tabs 
          value={tabValue} 
          onChange={handleTabChange}
          sx={{ borderBottom: 1, borderColor: 'divider' }}
        >
          <Tab label="Whitelist" />
          <Tab label="Blacklist" />
        </Tabs>

        {error && (
          <Alert severity="error" sx={{ mt: 2 }}>
            {error}
          </Alert>
        )}

        <TabPanel value={tabValue} index={0}>
          <Box sx={{ mb: 2 }}>
            <TextField
              fullWidth
              value={newUrl}
              onChange={(e) => setNewUrl(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Enter domain to whitelist (e.g., example.com)..."
              sx={{ mb: 1 }}
              error={!!error}
              helperText={error}
            />
            <Button 
              onClick={handleAdd} 
              disabled={!newUrl || loading}
              variant="contained"
            >
              Add Domain
            </Button>
          </Box>
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
            {localWhitelist.map((url, index) => (
              <Chip
                key={index}
                label={url}
                onDelete={() => handleRemove(url)}
                disabled={loading}
                color="primary"
                variant="outlined"
              />
            ))}
          </Box>
        </TabPanel>

        <TabPanel value={tabValue} index={1}>
          <Box sx={{ mb: 2 }}>
            <TextField
              fullWidth
              value={newUrl}
              onChange={(e) => setNewUrl(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Enter domain to blacklist (e.g., example.com)..."
              sx={{ mb: 1 }}
              error={!!error}
              helperText={error}
            />
            <Button 
              onClick={handleAdd} 
              disabled={!newUrl || loading}
              variant="contained"
            >
              Add Domain
            </Button>
          </Box>
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
            {localBlacklist.map((url, index) => (
              <Chip
                key={index}
                label={url}
                onDelete={() => handleRemove(url)}
                disabled={loading}
                color="error"
                variant="outlined"
              />
            ))}
          </Box>
        </TabPanel>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} disabled={loading}>
          Cancel
        </Button>
        <Button 
          onClick={handleSave} 
          variant="contained"
          disabled={loading}
        >
          {loading ? <CircularProgress size={24} /> : 'Save'}
        </Button>
      </DialogActions>
    </Dialog>
  );
}; 