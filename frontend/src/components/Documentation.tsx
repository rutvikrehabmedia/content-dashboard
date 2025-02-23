import React from 'react';
import {
  Box,
  Container,
  Typography,
  Paper,
  Grid,
  Card,
  CardContent,
  Divider,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
} from '@mui/material';
import {
  Search as SearchIcon,
  Download as ScraperIcon,
  Storage as StorageIcon,
  Code as CodeIcon,
  Settings as SettingsIcon,
} from '@mui/icons-material';

export const Documentation = () => {
  const sections = [
    {
      title: 'Search API',
      icon: <SearchIcon />,
      description: 'Learn how to use the search functionality',
      endpoints: [
        {
          method: 'POST',
          path: '/api/search',
          description: 'Search for content with optional filters'
        }
      ]
    },
    {
      title: 'Scraper API',
      icon: <ScraperIcon />,
      description: 'Extract content from web pages',
      endpoints: [
        {
          method: 'POST',
          path: '/api/scrape',
          description: 'Scrape content from a specific URL'
        }
      ]
    },
    {
      title: 'Storage API',
      icon: <StorageIcon />,
      description: 'Manage scraped content and search results',
      endpoints: [
        {
          method: 'GET',
          path: '/api/logs',
          description: 'Retrieve search and scraping logs'
        }
      ]
    }
  ];

  return (
    <Container maxWidth="xl">
      <Paper 
        elevation={0} 
        sx={{ 
          p: 4, 
          mb: 4, 
          bgcolor: 'primary.main',
          color: 'white'
        }}
      >
        <Typography variant="h4" gutterBottom>
          API Documentation
        </Typography>
        <Typography variant="subtitle1">
          Learn how to use our search and scraping APIs
        </Typography>
      </Paper>

      <Grid container spacing={4}>
        {sections.map((section, index) => (
          <Grid item xs={12} key={index}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <Box sx={{ color: 'primary.main', mr: 2 }}>
                    {section.icon}
                  </Box>
                  <Typography variant="h5">
                    {section.title}
                  </Typography>
                </Box>
                
                <Typography variant="body1" color="text.secondary" paragraph>
                  {section.description}
                </Typography>

                <Divider sx={{ my: 2 }} />

                <List>
                  {section.endpoints.map((endpoint, i) => (
                    <ListItem key={i}>
                      <ListItemIcon>
                        <CodeIcon color="primary" />
                      </ListItemIcon>
                      <ListItemText
                        primary={
                          <Box component="span" sx={{ fontFamily: 'monospace' }}>
                            {endpoint.method} {endpoint.path}
                          </Box>
                        }
                        secondary={endpoint.description}
                      />
                    </ListItem>
                  ))}
                </List>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
    </Container>
  );
}; 