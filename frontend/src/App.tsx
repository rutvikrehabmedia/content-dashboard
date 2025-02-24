import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider, CssBaseline, Box } from '@mui/material';
import { Header } from './components/Header';
import { Home } from './components/Home';
import { Search } from './components/Search';
import { BulkSearch } from './components/BulkSearch';
import { Scraper } from './components/Scraper';
import Logs from './components/Logs';
import { Documentation } from './components/Documentation';
import { Settings } from './components/Settings';
import { theme } from './theme';

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <Box sx={{ minHeight: '100vh', bgcolor: 'background.default' }}>
          <Header />
          <Box component="main" sx={{ py: 3 }}>
            <Routes>
              <Route path="/" element={<Home />} />
              <Route path="/search" element={<Search />} />
              <Route path="/bulk-search" element={<BulkSearch />} />
              <Route path="/scraper" element={<Scraper />} />
              <Route path="/settings" element={<Settings />} />
              <Route path="/logs" element={<Logs />} />
              <Route path="/docs" element={<Documentation />} />
            </Routes>
          </Box>
        </Box>
      </Router>
    </ThemeProvider>
  );
}

export default App; 