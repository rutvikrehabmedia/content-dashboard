export type StatusType = 'started' | 'processing' | 'completed' | 'failed' | 'error';

export const getStatusChipColor = (status: StatusType): "default" | "primary" | "secondary" | "error" | "info" | "success" | "warning" => {
  switch (status) {
    case 'completed':
      return 'success';
    case 'failed':
    case 'error':
      return 'error';
    case 'processing':
    case 'started':
      return 'info';
    default:
      return 'default';
  }
};

export const getStatusText = (status: StatusType): string => {
  switch (status) {
    case 'completed':
      return 'Completed';
    case 'failed':
      return 'Failed';
    case 'error':
      return 'Error';
    case 'processing':
      return 'Processing';
    case 'started':
      return 'Started';
    default:
      return 'Unknown';
  }
}; 