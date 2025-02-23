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
  IconButton
} from '@mui/material';
import { Add as AddIcon, Edit as EditIcon } from '@mui/icons-material';

interface ListDialogProps {
  open: boolean;
  onClose: () => void;
  whitelist: string[];
  blacklist: string[];
  onSave: (whitelist: string[], blacklist: string[]) => void;
  title?: string;
}

export const ListDialog: React.FC<ListDialogProps> = ({
  open,
  onClose,
  whitelist,
  blacklist,
  onSave,
  title = 'Manage Lists'
}) => {
  const [localWhitelist, setLocalWhitelist] = useState<string[]>(whitelist);
  const [localBlacklist, setLocalBlacklist] = useState<string[]>(blacklist);
  const [newUrl, setNewUrl] = useState('');
  const [activeList, setActiveList] = useState<'whitelist' | 'blacklist'>('whitelist');

  const handleAdd = () => {
    if (!newUrl) return;
    
    try {
      let urlToAdd = newUrl;
      if (!urlToAdd.startsWith('http://') && !urlToAdd.startsWith('https://')) {
        urlToAdd = 'https://' + urlToAdd;
      }
      
      new URL(urlToAdd);
      
      if (activeList === 'whitelist') {
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

  const handleRemove = (url: string, list: 'whitelist' | 'blacklist') => {
    if (list === 'whitelist') {
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
        <Box sx={{ mb: 3 }}>
          <Typography variant="h6" gutterBottom>
            {activeList === 'whitelist' ? 'Whitelist' : 'Blacklist'}
          </Typography>
          <TextField
            fullWidth
            value={newUrl}
            onChange={(e) => setNewUrl(e.target.value)}
            placeholder="Enter domain..."
            onKeyPress={(e) => e.key === 'Enter' && handleAdd()}
          />
          <Button
            onClick={handleAdd}
            startIcon={<AddIcon />}
            sx={{ mt: 1 }}
          >
            Add
          </Button>
        </Box>

        <Box sx={{ mb: 2 }}>
          <Typography variant="subtitle2" gutterBottom>
            Whitelist
          </Typography>
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
            {localWhitelist.map((url, index) => (
              <Chip
                key={index}
                label={url}
                onDelete={() => handleRemove(url, 'whitelist')}
                color="primary"
                variant="outlined"
              />
            ))}
          </Box>
        </Box>

        <Box>
          <Typography variant="subtitle2" gutterBottom>
            Blacklist
          </Typography>
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
            {localBlacklist.map((url, index) => (
              <Chip
                key={index}
                label={url}
                onDelete={() => handleRemove(url, 'blacklist')}
                color="error"
                variant="outlined"
              />
            ))}
          </Box>
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