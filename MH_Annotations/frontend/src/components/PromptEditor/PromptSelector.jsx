import React from 'react';
import {
  Card,
  CardContent,
  Typography,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Stack,
  Alert,
  Chip,
} from '@mui/material';
import {
  CheckCircle,
  Info as InfoIcon,
} from '@mui/icons-material';
import { ANNOTATOR_IDS, DOMAINS, DOMAIN_NAMES } from '../../utils/constants';

const PromptSelector = ({
  selectedAnnotator,
  selectedDomain,
  onAnnotatorChange,
  onDomainChange,
  isOverride,
  lastModified,
  loading,
}) => {
  const formatDate = (dateString) => {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleString();
  };

  return (
    <Card sx={{ mb: 2 }}>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Select Prompt
        </Typography>

        <Stack direction="row" spacing={2} sx={{ mb: 2 }}>
          <FormControl fullWidth>
            <InputLabel id="annotator-select-label">Annotator</InputLabel>
            <Select
              labelId="annotator-select-label"
              value={selectedAnnotator}
              onChange={(e) => onAnnotatorChange(e.target.value)}
              label="Annotator"
              disabled={loading}
            >
              {ANNOTATOR_IDS.map((id) => (
                <MenuItem key={id} value={id}>
                  Annotator {id}
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          <FormControl fullWidth>
            <InputLabel id="domain-select-label">Domain</InputLabel>
            <Select
              labelId="domain-select-label"
              value={selectedDomain}
              onChange={(e) => onDomainChange(e.target.value)}
              label="Domain"
              disabled={loading}
            >
              {DOMAINS.map((domain) => (
                <MenuItem key={domain} value={domain}>
                  {DOMAIN_NAMES[domain]}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Stack>

        {!loading && (
          <Alert
            severity={isOverride ? 'success' : 'info'}
            icon={isOverride ? <CheckCircle /> : <InfoIcon />}
            sx={{ mt: 2 }}
          >
            <Stack direction="row" spacing={1} alignItems="center">
              <Typography variant="body2">
                {isOverride
                  ? 'Using custom prompt override'
                  : 'Using base prompt (no override)'}
              </Typography>
              {isOverride && lastModified && (
                <Chip
                  size="small"
                  label={`Modified: ${formatDate(lastModified)}`}
                  variant="outlined"
                />
              )}
            </Stack>
          </Alert>
        )}
      </CardContent>
    </Card>
  );
};

export default PromptSelector;
