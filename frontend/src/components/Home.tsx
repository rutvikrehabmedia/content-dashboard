import React from 'react';
import {
  Box,
  Container,
  Typography,
  Paper,
  Grid,
  Card,
  CardContent,
  CardHeader,
  Button,
  useTheme
} from '@mui/material';
import {
  Search as SearchIcon,
  Download as ScraperIcon,
  Analytics as AnalyticsIcon,
  Speed as SpeedIcon
} from '@mui/icons-material';
import { Link } from 'react-router-dom';

export const Home = () => {
  const theme = useTheme();

  const features = [
    {
      icon: <SearchIcon fontSize="large" />,
      title: 'Intelligent Search',
      description: 'Advanced search capabilities with relevance scoring and content extraction'
    },
    {
      icon: <ScraperIcon fontSize="large" />,
      title: 'Smart Scraping',
      description: 'Automated web scraping with intelligent content parsing'
    },
    {
      icon: <AnalyticsIcon fontSize="large" />,
      title: 'Data Analytics',
      description: 'Comprehensive analytics and insights from scraped content'
    },
    {
      icon: <SpeedIcon fontSize="large" />,
      title: 'High Performance',
      description: 'Optimized for speed and reliability'
    }
  ];

  return (
    <Box>
      {/* Hero Section */}
      <Paper 
        elevation={0}
        sx={{
          bgcolor: 'primary.main',
          color: 'white',
          py: 8,
          mb: 6
        }}
      >
        <Container maxWidth="lg">
          <Grid container spacing={4} alignItems="center">
            <Grid item xs={12} md={7}>
              <Typography variant="h2" gutterBottom>
                Advanced Search & Scraping Platform
              </Typography>
              <Typography variant="h5" sx={{ mb: 4, opacity: 0.9 }}>
                Discover, analyze, and extract web content with intelligent automation
              </Typography>
              <Button
                component={Link}
                to="/search"
                variant="contained"
                size="large"
                sx={{
                  bgcolor: 'white',
                  color: 'primary.main',
                  '&:hover': {
                    bgcolor: 'grey.100',
                  }
                }}
              >
                Get Started
              </Button>
            </Grid>
          </Grid>
        </Container>
      </Paper>

      {/* Features Section */}
      <Container maxWidth="lg" sx={{ mb: 8 }}>
        <Grid container spacing={4}>
          {features.map((feature, index) => (
            <Grid item xs={12} sm={6} md={3} key={index}>
              <Card 
                elevation={0}
                sx={{
                  height: '100%',
                  display: 'flex',
                  flexDirection: 'column',
                  bgcolor: 'background.default'
                }}
              >
                <CardContent>
                  <Box sx={{ color: 'primary.main', mb: 2 }}>
                    {feature.icon}
                  </Box>
                  <Typography variant="h6" gutterBottom>
                    {feature.title}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {feature.description}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      </Container>
    </Box>
  );
}; 