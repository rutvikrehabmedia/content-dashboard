import React, { useState, useEffect } from 'react';
import {
  Box,
  TextField,
  Button,
  CircularProgress,
  Card,
  CardContent,
  Typography,
  Chip,
  Alert,
  Paper,
  Grid,
  IconButton,
  Tooltip,
  Divider,
  Collapse,
  Container,
  Tabs,
  Tab,
  FormControlLabel,
  Switch
} from '@mui/material';
import {
  Search as SearchIcon,
  ContentCopy as CopyIcon,
  OpenInNew as OpenInNewIcon,
  KeyboardArrowDown as ExpandMoreIcon,
  KeyboardArrowUp as ExpandLessIcon,
  Add as AddIcon,
  Delete as DeleteIcon
} from '@mui/icons-material';
import { searchAPI, SearchResult } from '../services/api';
import { RelevanceScore } from './RelevanceScore';
import { SearchResults } from './SearchResults';
import { ListManagementDialog } from './ListManagementDialog';
import { showNotification } from '../utils/notification';

const ResultCard: React.FC<{ result: SearchResult }> = ({ result }) => {
  const [expanded, setExpanded] = useState(false);

  const handleCopyContent = (url: string) => {
    navigator.clipboard.writeText(url);
    showNotification('URL copied to clipboard', 'success');
  };

  return (
    <Paper key={result._id} sx={{ p: 2, mb: 2 }}>
      <Typography variant="h6" gutterBottom>
        <a 
          href={result.url} 
          target="_blank" 
          rel="noopener noreferrer"
        >
          {result.title || result.url}
        </a>
      </Typography>
      
      {result.score !== undefined && (
        <Typography variant="body2" color="text.secondary">
          Relevance Score: {result.score.toFixed(2)}
        </Typography>
      )}

      <Box sx={{ display: 'flex', gap: 1 }}>
        <Tooltip title="Copy URL">
          <IconButton 
            size="small" 
            onClick={() => handleCopyContent(result.url)}
          >
            <CopyIcon />
          </IconButton>
        </Tooltip>
        <Tooltip title="Open in new tab">
          <IconButton 
            size="small" 
            component="a"
            href={result.url}
            target="_blank"
          >
            <OpenInNewIcon />
          </IconButton>
        </Tooltip>
      </Box>

      {result.error && (
        <Alert severity="error" sx={{ mt: 2 }}>
          {result.error}
        </Alert>
      )}
    </Paper>
  );
};

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

export const Search: React.FC = () => {
  const [tabValue, setTabValue] = useState(0);
  const [query, setQuery] = useState('');
  const [bulkQueries, setBulkQueries] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Whitelist/Blacklist states
  const [useGlobalLists, setUseGlobalLists] = useState(true);
  const [whitelist, setWhitelist] = useState<string[]>([]);
  const [blacklist, setBlacklist] = useState<string[]>([]);
  const [listDialogOpen, setListDialogOpen] = useState(false);

  useEffect(() => {
    // Fetch global whitelist and blacklist on component mount
    const fetchLists = async () => {
      try {
        const [whitelistData, blacklistData] = await Promise.all([
          searchAPI.getWhitelist(),
          searchAPI.getBlacklist()
        ]);
        setWhitelist(whitelistData.urls);
        setBlacklist(blacklistData.urls);
      } catch (err) {
        console.error('Error fetching lists:', err);
      }
    };
    fetchLists();
  }, []);

  const handleSearch = async () => {
    try {
      setLoading(true);
      setError(null);

      if (tabValue === 0) { // Single Search
        if (!query.trim()) {
          throw new Error('Please enter a search query');
        }

        const response = await searchAPI.search({
          query: query.trim(),
          whitelist: useGlobalLists ? [] : whitelist,
          blacklist: useGlobalLists ? [] : blacklist
        });
        setResults(response.results);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
    setResults([]);
    setError(null);
  };

  return (
    <Container maxWidth="xl">
      <Paper elevation={0} sx={{ p: 4, mb: 4, bgcolor: 'primary.main', color: 'white' }}>
        <Typography variant="h4" gutterBottom>
          Search
        </Typography>
        <Typography variant="subtitle1">
          Search through web content with customizable filters
        </Typography>
      </Paper>

      <Paper sx={{ mb: 4 }}>
        <Tabs 
          value={tabValue} 
          onChange={handleTabChange}
          sx={{ borderBottom: 1, borderColor: 'divider' }}
        >
          <Tab label="Single Search" />
        </Tabs>

        <Box sx={{ p: 3 }}>
          <Box sx={{ mb: 3 }}>
            <FormControlLabel
              control={
                <Switch
                  checked={useGlobalLists}
                  onChange={(e) => setUseGlobalLists(e.target.checked)}
                />
              }
              label="Use Global Whitelist/Blacklist"
            />

            {!useGlobalLists && (
              <Box sx={{ mt: 2 }}>
                <Typography variant="subtitle2" gutterBottom>
                  Custom Lists for this search:
                </Typography>
                <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
                  <Button
                    size="small"
                    onClick={() => setListDialogOpen(true)}
                    startIcon={<AddIcon />}
                  >
                    Manage Lists
                  </Button>
                </Box>
              </Box>
            )}
          </Box>

          <TabPanel value={tabValue} index={0}>
            <TextField
              fullWidth
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Enter your search query..."
              variant="outlined"
            />
          </TabPanel>

          <TabPanel value={tabValue} index={1}>
            <TextField
              fullWidth
              multiline
              rows={10}
              value={bulkQueries}
              onChange={(e) => setBulkQueries(e.target.value)}
              placeholder="Enter one search query per line..."
              variant="outlined"
            />
          </TabPanel>

          <Box sx={{ mt: 3 }}>
            <Button
              variant="contained"
              onClick={handleSearch}
              disabled={loading}
              sx={{ minWidth: 150 }}
            >
              {loading ? (
                <CircularProgress size={24} color="inherit" />
              ) : (
                'Search'
              )}
            </Button>
          </Box>
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
          loading={loading}
          error={error}
        />
      )}

      <ListManagementDialog
        open={listDialogOpen}
        onClose={() => setListDialogOpen(false)}
        whitelist={whitelist}
        blacklist={blacklist}
        onSaveWhitelist={setWhitelist}
        onSaveBlacklist={setBlacklist}
        isGlobal={useGlobalLists}
      />
    </Container>
  );
}; 