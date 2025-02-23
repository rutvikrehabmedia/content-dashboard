import React from 'react';
import { Link } from 'react-router-dom';
import { Button } from '@mui/material';

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
    </div>
  );
};

export default Navbar; 