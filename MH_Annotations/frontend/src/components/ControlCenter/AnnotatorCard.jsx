import React, { useState } from 'react';
import {
  Card,
  CardHeader,
  CardContent,
  Collapse,
  IconButton,
  Typography,
  Box,
  Chip,
  Divider,
  List,
  ListItem,
  ListItemText,
  Alert,
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Code as CodeIcon,
} from '@mui/icons-material';

const AnnotatorCard = ({ annotatorSummary }) => {
  const [expanded, setExpanded] = useState(false);

  const {
    annotator_id,
    has_api_key,
    global_settings,
    enabled_domains,
    total_target_count,
    enabled_count,
  } = annotatorSummary;

  const handleExpandClick = () => {
    setExpanded(!expanded);
  };

  const getSourceTypeLabel = (sourceType) => {
    switch (sourceType) {
      case 'version':
        return 'Custom Version';
      case 'override':
        return 'Override';
      case 'base':
      default:
        return 'Base Prompt';
    }
  };

  const getSourceTypeColor = (sourceType) => {
    switch (sourceType) {
      case 'version':
        return 'primary';
      case 'override':
        return 'warning';
      case 'base':
      default:
        return 'default';
    }
  };

  return (
    <Card
      elevation={3}
      sx={{
        position: 'relative',
        transition: 'transform 0.2s, box-shadow 0.2s',
        '&:hover': {
          transform: 'translateY(-2px)',
          boxShadow: 6,
        },
      }}
    >
      <CardHeader
        title={
          <Box display="flex" alignItems="center" gap={1}>
            <Typography variant="h6" component="span">
              Annotator {annotator_id}
            </Typography>
            {has_api_key ? (
              <CheckCircleIcon color="success" fontSize="small" />
            ) : (
              <ErrorIcon color="error" fontSize="small" />
            )}
          </Box>
        }
        subheader={
          <Box display="flex" flexDirection="column" gap={0.5} mt={1}>
            <Typography variant="body2" color="text.secondary">
              {enabled_count} domain{enabled_count !== 1 ? 's' : ''} enabled
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Total target: {total_target_count} samples
            </Typography>
          </Box>
        }
        action={
          <IconButton
            onClick={handleExpandClick}
            aria-expanded={expanded}
            aria-label="show more"
            sx={{
              transform: expanded ? 'rotate(180deg)' : 'rotate(0deg)',
              transition: 'transform 0.3s',
            }}
          >
            <ExpandMoreIcon />
          </IconButton>
        }
      />

      <Collapse in={expanded} timeout="auto" unmountOnExit>
        <CardContent>
          {/* API Key Status */}
          <Box mb={2}>
            <Typography variant="subtitle2" gutterBottom>
              API Key Status
            </Typography>
            {has_api_key ? (
              <Chip
                icon={<CheckCircleIcon />}
                label="API Key Configured"
                color="success"
                size="small"
              />
            ) : (
              <Alert severity="error" sx={{ mt: 1 }}>
                No API key configured for this annotator
              </Alert>
            )}
          </Box>

          <Divider sx={{ my: 2 }} />

          {/* Global Settings */}
          <Box mb={2}>
            <Typography variant="subtitle2" gutterBottom>
              Global Settings
            </Typography>
            <Box
              sx={{
                bgcolor: 'grey.50',
                borderRadius: 1,
                p: 1.5,
                mt: 1,
                border: '1px solid',
                borderColor: 'grey.200',
              }}
            >
              <Typography variant="body2" color="text.secondary">
                Model: <strong>{global_settings?.model_name || 'N/A'}</strong>
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Request Delay:{' '}
                <strong>{global_settings?.request_delay_seconds || 0}s</strong>
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Max Retries: <strong>{global_settings?.max_retries || 0}</strong>
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Crash Detection:{' '}
                <strong>{global_settings?.crash_detection_minutes || 0}min</strong>
              </Typography>
            </Box>
          </Box>

          <Divider sx={{ my: 2 }} />

          {/* Enabled Domains */}
          <Box>
            <Typography variant="subtitle2" gutterBottom>
              Enabled Domains ({enabled_count})
            </Typography>
            {enabled_domains && enabled_domains.length > 0 ? (
              <List dense disablePadding>
                {enabled_domains.map((domainConfig, index) => (
                  <ListItem
                    key={domainConfig.domain}
                    sx={{
                      bgcolor: index % 2 === 0 ? 'grey.50' : 'white',
                      borderRadius: 1,
                      mb: 1,
                      border: '1px solid',
                      borderColor: 'grey.200',
                    }}
                  >
                    <ListItemText
                      primary={
                        <Box display="flex" alignItems="center" gap={1}>
                          <Typography variant="body2" fontWeight="medium">
                            {domainConfig.domain.charAt(0).toUpperCase() +
                              domainConfig.domain.slice(1)}
                          </Typography>
                          <Chip
                            size="small"
                            label={getSourceTypeLabel(
                              domainConfig.prompt_info?.source_type
                            )}
                            color={getSourceTypeColor(
                              domainConfig.prompt_info?.source_type
                            )}
                            icon={<CodeIcon />}
                          />
                        </Box>
                      }
                      secondary={
                        <Box mt={0.5}>
                          <Typography variant="caption" color="text.secondary">
                            Target: {domainConfig.target_count} samples
                          </Typography>
                          {domainConfig.prompt_info?.active_version && (
                            <Typography
                              variant="caption"
                              color="primary"
                              display="block"
                            >
                              Version: {domainConfig.prompt_info.active_version}
                            </Typography>
                          )}
                          {domainConfig.prompt_info?.content_preview && (
                            <Typography
                              variant="caption"
                              color="text.secondary"
                              display="block"
                              sx={{
                                mt: 0.5,
                                fontStyle: 'italic',
                                maxWidth: '100%',
                                overflow: 'hidden',
                                textOverflow: 'ellipsis',
                                whiteSpace: 'nowrap',
                              }}
                            >
                              "{domainConfig.prompt_info.content_preview}"
                            </Typography>
                          )}
                        </Box>
                      }
                    />
                  </ListItem>
                ))}
              </List>
            ) : (
              <Alert severity="info" sx={{ mt: 1 }}>
                No domains enabled for this annotator
              </Alert>
            )}
          </Box>
        </CardContent>
      </Collapse>
    </Card>
  );
};

export default AnnotatorCard;
