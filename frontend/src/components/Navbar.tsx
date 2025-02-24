import React from 'react';
import { Link } from 'react-router-dom';
import { Button } from '@mui/material';
import ListAltIcon from '@mui/icons-material/ListAlt';

const Navbar: React.FC = () => {
  return (
    <div>
      {/* Add your existing content here */}
      <Button
        component={Link}
        to="/bulk-search"
        color="inherit"
      >
        Bulk Search
      </Button>
      <Button
        component={Link}
        to="/scrape-logs"
        color="inherit"
        startIcon={<ListAltIcon />}
      >
        Scrape Logs
      </Button>
    </div>
  );
};

export default Navbar; 