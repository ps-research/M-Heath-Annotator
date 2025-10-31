import React from 'react';
import { Paper, Box, Typography, Chip, Stack, Divider } from '@mui/material';
import { CheckCircle, Error as ErrorIcon } from '@mui/icons-material';

const PromptMetadata = ({ content }) => {
  const characterCount = content?.length || 0;
  const lineCount = content ? content.split('\n').length : 0;
  const wordCount = content
    ? content.split(/\s+/).filter((word) => word.length > 0).length
    : 0;
  const hasPlaceholder = content ? content.includes('{text}') : false;

  const formatNumber = (num) => {
    return num.toLocaleString();
  };

  return (
    <Paper sx={{ p: 2, mb: 2 }}>
      <Stack
        direction="row"
        spacing={3}
        alignItems="center"
        divider={<Divider orientation="vertical" flexItem />}
      >
        <Box>
          <Typography variant="caption" color="text.secondary">
            Characters
          </Typography>
          <Typography variant="h6">{formatNumber(characterCount)}</Typography>
        </Box>

        <Box>
          <Typography variant="caption" color="text.secondary">
            Lines
          </Typography>
          <Typography variant="h6">{formatNumber(lineCount)}</Typography>
        </Box>

        <Box>
          <Typography variant="caption" color="text.secondary">
            Words
          </Typography>
          <Typography variant="h6">{formatNumber(wordCount)}</Typography>
        </Box>

        <Box sx={{ flexGrow: 1 }}>
          <Chip
            icon={hasPlaceholder ? <CheckCircle /> : <ErrorIcon />}
            label={
              hasPlaceholder
                ? 'Contains {text} placeholder'
                : 'Missing {text} placeholder'
            }
            color={hasPlaceholder ? 'success' : 'error'}
            variant="outlined"
          />
        </Box>
      </Stack>
    </Paper>
  );
};

export default PromptMetadata;
