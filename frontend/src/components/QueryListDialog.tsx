import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  Chip,
  Box,
  Typography,
  Tabs,
  Tab
} from '@mui/material';

interface QueryListDialogProps {
  open: boolean;
  onClose: () => void;
  whitelist: string[];
  blacklist: string[];
  onSave: (whitelist: string[], blacklist: string[]) => void;
  title?: string;
}

export const QueryListDialog: React.FC<QueryListDialogProps> = ({
  open,
  onClose,
  whitelist,
  blacklist,
  onSave,
  title = 'Manage Query Lists'
}) => {
  const [localWhitelist, setLocalWhitelist] = useState<string[]>(whitelist);
  const [localBlacklist, setLocalBlacklist] = useState<string[]>(blacklist);
  const [newUrl, setNewUrl] = useState('');
  const [tabValue, setTabValue] = useState(0);

  const handleAdd = () => {
    if (!newUrl) return;
    
    try {
      let urlToAdd = newUrl;
      if (!urlToAdd.startsWith('http://') && !urlToAdd.startsWith('https://')) {
        urlToAdd = 'https://' + urlToAdd;
      }
      
      new URL(urlToAdd);
      
      if (tabValue === 0) {
        if (!localWhitelist.includes(urlToAdd)) {
          setLocalWhitelist([...localWhitelist, urlToAdd]);
        }
      } else {
        if (!localBlacklist.includes(urlToAdd)) {
          setLocalBlacklist([...localBlacklist, urlToAdd]);
        }
      }
      setNewUrl('');
    } catch (err) {
      // Handle invalid URL
    }
  };

  const handleRemove = (url: string) => {
    if (tabValue === 0) {
      setLocalWhitelist(localWhitelist.filter(u => u !== url));
    } else {
      setLocalBlacklist(localBlacklist.filter(u => u !== url));
    }
  };

  const handleSave = () => {
    onSave(localWhitelist, localBlacklist);
    onClose();
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>{title}</DialogTitle>
      <DialogContent>
        <Tabs value={tabValue} onChange={(_, newValue) => setTabValue(newValue)} sx={{ mb: 2 }}>
          <Tab label="Whitelist" />
          <Tab label="Blacklist" />
        </Tabs>

        <Box sx={{ mb: 3 }}>
          <TextField
            fullWidth
            value={newUrl}
            onChange={(e) => setNewUrl(e.target.value)}
            placeholder={`Enter domain to ${tabValue === 0 ? 'whitelist' : 'blacklist'}...`}
            onKeyPress={(e) => e.key === 'Enter' && handleAdd()}
          />
          <Button
            onClick={handleAdd}
            variant="contained"
            sx={{ mt: 1 }}
          >
            Add Domain
          </Button>
        </Box>

        <Box>
          {tabValue === 0 ? (
            <Box>
              <Typography variant="subtitle2" gutterBottom>
                Whitelisted Domains
              </Typography>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                {localWhitelist.map((url, index) => (
                  <Chip
                    key={index}
                    label={url}
                    onDelete={() => handleRemove(url)}
                    color="primary"
                    variant="outlined"
                  />
                ))}
              </Box>
            </Box>
          ) : (
            <Box>
              <Typography variant="subtitle2" gutterBottom>
                Blacklisted Domains
              </Typography>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                {localBlacklist.map((url, index) => (
                  <Chip
                    key={index}
                    label={url}
                    onDelete={() => handleRemove(url)}
                    color="error"
                    variant="outlined"
                  />
                ))}
              </Box>
            </Box>
          )}
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button onClick={handleSave} variant="contained">
          Save
        </Button>
      </DialogActions>
    </Dialog>
  );
}; 