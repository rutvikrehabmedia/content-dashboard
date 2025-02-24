import { createBrowserRouter } from 'react-router-dom';
import { Layout } from '../components/Layout';
import { Search } from '../components/Search';
import { BulkSearch } from '../components/BulkSearch';
import { Settings } from '../components/Settings';
import { Logs } from '../components/Logs';

export const router = createBrowserRouter([
  {
    path: '/',
    element: <Layout />,
    children: [
      {
        path: '/',
        element: <Search />,
      },
      {
        path: '/bulk-search',
        element: <BulkSearch />,
      },
      {
        path: '/settings',
        element: <Settings />,
      },
      {
        path: '/logs',
        element: <Logs />,
      },
    ],
  },
]); 