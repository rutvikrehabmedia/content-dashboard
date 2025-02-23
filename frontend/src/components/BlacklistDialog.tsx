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

interface BlacklistDialogProps {
  open: boolean;
  onClose: () => void;
  blacklist: string[];
  onSave: (blacklist: string[]) => void;
}

export const BlacklistDialog: React.FC<BlacklistDialogProps> = ({
  open,
  onClose,
  blacklist,
  onSave
}) => {
  const [newUrl, setNewUrl] = useState('');
  const [localBlacklist, setLocalBlacklist] = useState([...blacklist]);

  const handleAdd = () => {
    if (newUrl && !localBlacklist.includes(newUrl)) {
      setLocalBlacklist([...localBlacklist, newUrl]);
      setNewUrl('');
    }
  };

  const handleRemove = (urlToRemove: string) => {
    setLocalBlacklist(localBlacklist.filter(url => url !== urlToRemove));
  };

  const handleSave = () => {
    onSave(localBlacklist);
    onClose();
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>Manage Blacklist</DialogTitle>
      <DialogContent>
        <Box sx={{ mb: 2 }}>
          <TextField
            fullWidth
            value={newUrl}
            onChange={(e) => setNewUrl(e.target.value)}
            placeholder="Enter URL to blacklist..."
            sx={{ mb: 1 }}
          />
          <Button onClick={handleAdd} disabled={!newUrl}>
            Add URL
          </Button>
        </Box>
        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
          {localBlacklist.map((url, index) => (
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