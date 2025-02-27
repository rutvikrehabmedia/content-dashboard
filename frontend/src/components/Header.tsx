import React from 'react';
import {
  AppBar,
  Toolbar,
  Button,
  Typography,
  Box,
  Container,
  useTheme
} from '@mui/material';
import {
  Home as HomeIcon,
  Search as SearchIcon,
  Download as ScraperIcon,
  History as LogsIcon,
  Book as DocsIcon,
  List as ListIcon,
  ViewList as BulkIcon,
  Settings as SettingsIcon,
  ListAlt as ListAltIcon
} from '@mui/icons-material';
import { Link, useLocation } from 'react-router-dom';

export const Header: React.FC = () => {
  const theme = useTheme();
  const location = useLocation();

  const navItems = [
    { path: '/', label: 'Home', icon: <HomeIcon /> },
    { path: '/search', label: 'Search', icon: <SearchIcon /> },
    { path: '/bulk-search', label: 'Bulk Search', icon: <BulkIcon /> },
    { path: '/logs', label: 'Logs', icon: <LogsIcon /> },
    { path: '/scraper', label: 'Scraper', icon: <ScraperIcon /> },
    { path: '/bulk-scrape', label: 'Bulk Scraper', icon: <ScraperIcon /> },
    { path: '/scrape-logs', label: 'Scrape Logs', icon: <ListAltIcon /> },
    { path: '/settings', label: 'Settings', icon: <SettingsIcon /> },
    { path: '/docs', label: 'Documentation', icon: <DocsIcon /> },
  ];

  return (
    <AppBar position="sticky" elevation={0} sx={{ backgroundColor: 'white' }}>
      <Container maxWidth="xl">
        <Toolbar disableGutters>
          <Typography
            variant="h6"
            component={Link}
            to="/"
            sx={{
              mr: 4,
              color: theme.palette.primary.main,
              textDecoration: 'none',
              fontWeight: 700,
            }}
          >
            Search Dashboard
          </Typography>

          <Box sx={{ flexGrow: 1, display: 'flex', gap: 1 }}>
            {navItems.map((item) => (
              <Button
                key={item.path}
                component={Link}
                to={item.path}
                startIcon={item.icon}
                sx={{
                  color: location.pathname === item.path ? 'primary.main' : 'text.primary',
                  borderRadius: '8px',
                  px: 2,
                  '&:hover': {
                    backgroundColor: 'rgba(33, 150, 243, 0.08)',
                  },
                }}
              >
                {item.label}
              </Button>
            ))}
          </Box>
        </Toolbar>
      </Container>
    </AppBar>
  );
}; 