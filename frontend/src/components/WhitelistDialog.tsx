import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  Box,
  Chip
} from '@mui/material';

interface WhitelistDialogProps {
  open: boolean;
  onClose: () => void;
  whitelist: string[];
  onSave: (whitelist: string[]) => void;
}

export const WhitelistDialog: React.FC<WhitelistDialogProps> = ({
  open,
  onClose,
  whitelist,
  onSave
}) => {
  const [newUrl, setNewUrl] = useState('');
  const [localWhitelist, setLocalWhitelist] = useState([...whitelist]);

  const handleAdd = () => {
    if (newUrl && !localWhitelist.includes(newUrl)) {
      setLocalWhitelist([...localWhitelist, newUrl]);
      setNewUrl('');
    }
  };

  const handleRemove = (urlToRemove: string) => {
    setLocalWhitelist(localWhitelist.filter(url => url !== urlToRemove));
  };

  const handleSave = () => {
    onSave(localWhitelist);
    onClose();
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>Manage Whitelist</DialogTitle>
      <DialogContent>
        <Box sx={{ mb: 2 }}>
          <TextField
            fullWidth
            value={newUrl}
            onChange={(e) => setNewUrl(e.target.value)}
            placeholder="Enter URL to whitelist..."
            sx={{ mb: 1 }}
          />
          <Button onClick={handleAdd} disabled={!newUrl}>
            Add URL
          </Button>
        </Box>
        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
          {localWhitelist.map((url, index) => (
            <Chip
              key={index}
              label={url}
              onDelete={() => handleRemove(url)}
            />
          ))}
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