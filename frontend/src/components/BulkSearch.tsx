import React, { useState, useEffect } from 'react';
import {
  Box,
  Container,
  Typography,
  Paper,
  TextField,
  Button,
  Alert,
  CircularProgress,
  Tabs,
  Tab,
  Divider,
  FormControlLabel,
  Switch,
  IconButton,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions
} from '@mui/material';
import {
  CloudUpload as UploadIcon,
  CloudDownload as DownloadIcon,
  Delete as DeleteIcon,
  Add as AddIcon,
  List as ListIcon,
  ContentCopy as ContentCopyIcon
} from '@mui/icons-material';
import { SearchResults } from './SearchResults';
import { searchAPI, SearchResult } from '../services/api';
import { ListManagementDialog } from './ListManagementDialog';
import { QueryListDialog } from './QueryListDialog';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

const TabPanel: React.FC<TabPanelProps> = ({ children, value, index }) => (
  <div role="tabpanel" hidden={value !== index}>
    {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
  </div>
);

interface QueryEntry {
  query: string;
  whitelist: string[];
  blacklist: string[];
}

export const BulkSearch: React.FC = () => {
  const [queryEntries, setQueryEntries] = useState<QueryEntry[]>([{
    query: '',
    whitelist: [],
    blacklist: []
  }]);
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [useGlobalLists, setUseGlobalLists] = useState(true);
  const [globalWhitelist, setGlobalWhitelist] = useState<string[]>([]);
  const [globalBlacklist, setGlobalBlacklist] = useState<string[]>([]);
  const [activeQueryDialog, setActiveQueryDialog] = useState<number | null>(null);
  const [processId, setProcessId] = useState<string | null>(null);
  const [processDialog, setProcessDialog] = useState(false);

  useEffect(() => {
    // Fetch global lists on mount
    const fetchGlobalLists = async () => {
      try {
        const [whitelistData, blacklistData] = await Promise.all([
          searchAPI.getWhitelist(),
          searchAPI.getBlacklist()
        ]);
        setGlobalWhitelist(whitelistData.urls);
        setGlobalBlacklist(blacklistData.urls);
      } catch (err) {
        console.error('Error fetching global lists:', err);
      }
    };
    fetchGlobalLists();
  }, []);

  const handleAddEntry = () => {
    setQueryEntries([...queryEntries, { query: '', whitelist: [], blacklist: [] }]);
  };

  const handleRemoveEntry = (index: number) => {
    setQueryEntries(queryEntries.filter((_, i) => i !== index));
  };

  const handleEntryChange = (index: number, field: keyof QueryEntry, value: string | string[]) => {
    const newEntries = [...queryEntries];
    newEntries[index] = {
      ...newEntries[index],
      [field]: value
    };
    setQueryEntries(newEntries);
  };

  const handleListsChange = (index: number, whitelist: string[], blacklist: string[]) => {
    const newEntries = [...queryEntries];
    newEntries[index] = {
      ...newEntries[index],
      whitelist,
      blacklist
    };
    setQueryEntries(newEntries);
    setActiveQueryDialog(null);
  };

  const handleBulkSearch = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await searchAPI.bulkSearch({
        queries: queryEntries,
        globalListsEnabled: useGlobalLists,
        globalWhitelist,
        globalBlacklist
      });

      setProcessId(response.process_id);
      setProcessDialog(true);
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start bulk search');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container maxWidth="xl">
      <Paper elevation={0} sx={{ p: 4, mb: 4, bgcolor: 'primary.main', color: 'white' }}>
        <Typography variant="h4" gutterBottom>
          Bulk Search
        </Typography>
        <Typography variant="subtitle1">
          Search multiple queries with custom filters
        </Typography>
      </Paper>

      <Paper sx={{ p: 3, mb: 3 }}>
        <Box sx={{ mb: 3 }}>
          <FormControlLabel
            control={
              <Switch
                checked={useGlobalLists}
                onChange={(e) => setUseGlobalLists(e.target.checked)}
              />
            }
            label="Use Global Lists"
          />
        </Box>

        {queryEntries.map((entry, index) => (
          <Paper key={index} sx={{ p: 2, mb: 2, bgcolor: 'background.default' }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
              <Typography variant="h6">Query {index + 1}</Typography>
              {queryEntries.length > 1 && (
                <IconButton onClick={() => handleRemoveEntry(index)} color="error">
                  <DeleteIcon />
                </IconButton>
              )}
            </Box>

            <TextField
              fullWidth
              label="Search Query"
              value={entry.query}
              onChange={(e) => handleEntryChange(index, 'query', e.target.value)}
              sx={{ mb: 2 }}
            />

            <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
              <Button
                variant="outlined"
                onClick={() => setActiveQueryDialog(index)}
                startIcon={<ListIcon />}
              >
                Manage Lists
              </Button>
            </Box>

            <QueryListDialog
              open={activeQueryDialog === index}
              onClose={() => setActiveQueryDialog(null)}
              whitelist={entry.whitelist}
              blacklist={entry.blacklist}
              onSave={(whitelist, blacklist) => handleListsChange(index, whitelist, blacklist)}
              title={`Lists for Query ${index + 1}`}
            />
          </Paper>
        ))}

        <Button
          startIcon={<AddIcon />}
          onClick={handleAddEntry}
          sx={{ mt: 2 }}
        >
          Add Query
        </Button>

        <Box sx={{ mt: 3 }}>
          <Button
            variant="contained"
            onClick={handleBulkSearch}
            disabled={loading}
          >
            {loading ? <CircularProgress size={24} /> : 'Search All'}
          </Button>
        </Box>
      </Paper>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {results.length > 0 && (
        <SearchResults 
          results={results}
          query={queryEntries.map(e => e.query).join(', ')}
          loading={loading}
          error={error}
        />
      )}

      <Dialog open={processDialog} onClose={() => setProcessDialog(false)}>
        <DialogTitle>Bulk Search Started</DialogTitle>
        <DialogContent>
          <Typography>
            Your bulk search has been started. You can track its progress using this ID:
          </Typography>
          <Box sx={{ 
            my: 2, 
            p: 2, 
            bgcolor: 'grey.100', 
            borderRadius: 1,
            display: 'flex',
            alignItems: 'center',
            gap: 1
          }}>
            <Typography fontFamily="monospace">{processId}</Typography>
            <IconButton size="small" onClick={() => {
              navigator.clipboard.writeText(processId || '');
            }}>
              <ContentCopyIcon fontSize="small" />
            </IconButton>
          </Box>
          <Typography>
            View progress in the Logs section.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setProcessDialog(false)}>Close</Button>
          <Button 
            variant="contained"
            onClick={() => {
              setProcessDialog(false);
              navigate('/logs');
            }}
          >
            Go to Logs
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
}; 