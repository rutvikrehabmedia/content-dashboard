import React from 'react';
import { Chip, ChipProps } from '@mui/material';

interface RelevanceScoreProps {
  score: number;
}

export const RelevanceScore: React.FC<RelevanceScoreProps> = ({ score }) => {
  const getScoreColor = (score: number): ChipProps['color'] => {
    if (score > 0.7) return 'success';
    if (score > 0.4) return 'warning';
    return 'error';
  };

  const getScoreLabel = (score: number): string => {
    const percentage = (score * 100).toFixed(1);
    return `Score: ${percentage}%`;
  };

  return (
    <Chip
      label={getScoreLabel(score)}
      color={getScoreColor(score)}
      size="small"
      sx={{ mb: 1 }}
    />
  );
}; 