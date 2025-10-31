import React, { useState, useEffect } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import {
  Card,
  CardContent,
  Typography,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Checkbox,
  FormControlLabel,
  Slider,
  TextField,
  Button,
  Stack,
  Box,
  Alert,
  LinearProgress,
  CircularProgress,
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  Save as SaveIcon,
} from '@mui/icons-material';
import {
  updateDomainConfig,
  selectAnnotatorSettings,
  selectIsLoading,
  selectErrors,
} from '../../store/slices/configSlice';
import { ANNOTATOR_IDS, DOMAINS, DOMAIN_NAMES, SAMPLE_LIMIT } from '../../utils/constants';

const SampleLimitSliders = () => {
  const dispatch = useDispatch();
  const annotatorSettings = useSelector(selectAnnotatorSettings);
  const loading = useSelector(selectIsLoading);
  const errors = useSelector(selectErrors);

  const [localConfigs, setLocalConfigs] = useState({});
  const [hasChanges, setHasChanges] = useState(false);

  // Initialize local state from Redux
  useEffect(() => {
    // Guard clause: don't initialize if settings haven't loaded yet
    if (!annotatorSettings || Object.keys(annotatorSettings).length === 0) {
      return;
      }
    const newConfigs = {};
    ANNOTATOR_IDS.forEach((annotatorId) => {
      newConfigs[annotatorId] = {};
      DOMAINS.forEach((domain) => {
        const config = annotatorSettings[annotatorId]?.[domain] || {
          enabled: false,
          target_count: 0,
        };
        newConfigs[annotatorId][domain] = { ...config };
      });
    });
    setLocalConfigs(newConfigs);
  }, [annotatorSettings]);

  // Check for unsaved changes
  useEffect(() => {

    // Guard clause: don't check if settings haven't loaded yet
    if (!annotatorSettings || Object.keys(annotatorSettings).length === 0) {
      return;
    }
    const changed = ANNOTATOR_IDS.some((annotatorId) =>
      DOMAINS.some((domain) => {
        const reduxConfig = annotatorSettings[annotatorId]?.[domain];
        const localConfig = localConfigs[annotatorId]?.[domain];
        return (
          JSON.stringify(reduxConfig) !== JSON.stringify(localConfig)
        );
      })
    );
    setHasChanges(changed);
  }, [localConfigs, annotatorSettings]);

  const handleEnabledChange = (annotatorId, domain, enabled) => {
    setLocalConfigs((prev) => ({
      ...prev,
      [annotatorId]: {
        ...(prev[annotatorId] || {}),
        [domain]: {
          ...(prev[annotatorId]?.[domain] || { enabled: false, target_count: 0 }),
          enabled,
        },
      },
    }));
  };

  const handleTargetCountChange = (annotatorId, domain, value) => {
    // Ensure value is within bounds and a multiple of 5
    let newValue = Math.max(SAMPLE_LIMIT.MIN, Math.min(SAMPLE_LIMIT.MAX, value));
    newValue = Math.round(newValue / SAMPLE_LIMIT.STEP) * SAMPLE_LIMIT.STEP;

    setLocalConfigs((prev) => ({
      ...prev,
      [annotatorId]: {
        ...(prev[annotatorId] || {}),
        [domain]: {
          ...(prev[annotatorId]?.[domain] || { enabled: false, target_count: 0 }),
          target_count: newValue,
        },
      },
    }));
  };

  const calculateAnnotatorTotal = (annotatorId) => {
    if (!localConfigs[annotatorId]) return 0;
    return DOMAINS.reduce((sum, domain) => {
      const config = localConfigs[annotatorId][domain];
      return sum + (config?.enabled ? config.target_count : 0);
    }, 0);
  };

  const calculateGrandTotal = () => {
    return ANNOTATOR_IDS.reduce(
      (sum, annotatorId) => sum + calculateAnnotatorTotal(annotatorId),
      0
    );
  };

  const handleSave = async () => {
    const promises = [];

    // Guard clause: don't save if settings haven't loaded yet
    if (!annotatorSettings || Object.keys(annotatorSettings).length === 0) {
      return;
    }

    ANNOTATOR_IDS.forEach((annotatorId) => {
      DOMAINS.forEach((domain) => {
        const reduxConfig = annotatorSettings[annotatorId]?.[domain];
        const localConfig = localConfigs[annotatorId]?.[domain];

        if (JSON.stringify(reduxConfig) !== JSON.stringify(localConfig)) {
          promises.push(
            dispatch(
              updateDomainConfig({
                annotatorId,
                domain,
                config: localConfig,
              })
            )
          );
        }
      });
    });

    try {
      await Promise.all(promises);
    } catch (error) {
      // Error handled by Redux state
    }
  };

  const totalAcrossAll = calculateGrandTotal();
  const maxPossible = ANNOTATOR_IDS.length * DOMAINS.length * SAMPLE_LIMIT.MAX;

  return (
    <Card sx={{ mb: 3 }}>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Sample Limits
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
          Configure target sample counts for each annotator-domain combination
        </Typography>

        <Stack spacing={2}>
          {ANNOTATOR_IDS.map((annotatorId) => {
            const annotatorTotal = calculateAnnotatorTotal(annotatorId);
            const maxForAnnotator = DOMAINS.length * SAMPLE_LIMIT.MAX;

            return (
              <Accordion key={annotatorId}>
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Box sx={{ flexGrow: 1 }}>
                    <Typography variant="subtitle1">
                      Annotator {annotatorId}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {annotatorTotal.toLocaleString()} / {maxForAnnotator.toLocaleString()} samples
                    </Typography>
                  </Box>
                  <LinearProgress
                    variant="determinate"
                    value={(annotatorTotal / maxForAnnotator) * 100}
                    sx={{ width: 100, mt: 1, mr: 2 }}
                  />
                </AccordionSummary>
                <AccordionDetails>
                  <Stack spacing={2}>
                    {DOMAINS.map((domain) => {
                      const config = localConfigs[annotatorId]?.[domain] || {
                        enabled: false,
                        target_count: 0,
                      };

                      return (
                        <Box key={domain}>
                          <FormControlLabel
                            control={
                              <Checkbox
                                checked={config.enabled}
                                onChange={(e) =>
                                  handleEnabledChange(
                                    annotatorId,
                                    domain,
                                    e.target.checked
                                  )
                                }
                              />
                            }
                            label={
                              <Typography variant="body2">
                                {DOMAIN_NAMES[domain]}
                              </Typography>
                            }
                          />
                          <Stack
                            direction="row"
                            spacing={2}
                            alignItems="center"
                            sx={{ ml: 4 }}
                          >
                            <Slider
                              value={config.target_count}
                              onChange={(e, value) =>
                                handleTargetCountChange(annotatorId, domain, value)
                              }
                              disabled={!config.enabled}
                              min={SAMPLE_LIMIT.MIN}
                              max={SAMPLE_LIMIT.MAX}
                              step={SAMPLE_LIMIT.STEP}
                              marks={[
                                { value: 0, label: '0' },
                                { value: 500, label: '500' },
                                { value: 1000, label: '1000' },
                                { value: 1500, label: '1500' },
                                { value: 2000, label: '2000' },
                              ]}
                              valueLabelDisplay="auto"
                              sx={{ flexGrow: 1 }}
                            />
                            <TextField
                              type="number"
                              value={config.target_count}
                              onChange={(e) =>
                                handleTargetCountChange(
                                  annotatorId,
                                  domain,
                                  parseInt(e.target.value) || 0
                                )
                              }
                              disabled={!config.enabled}
                              size="small"
                              sx={{ width: 100 }}
                              InputProps={{
                                inputProps: {
                                  min: SAMPLE_LIMIT.MIN,
                                  max: SAMPLE_LIMIT.MAX,
                                  step: SAMPLE_LIMIT.STEP,
                                },
                              }}
                            />
                          </Stack>
                          {config.enabled && config.target_count > 2000 && (
                            <Alert severity="warning" sx={{ mt: 1, ml: 4 }}>
                              Warning: Target count exceeds typical dataset size (2000)
                            </Alert>
                          )}
                        </Box>
                      );
                    })}
                  </Stack>
                </AccordionDetails>
              </Accordion>
            );
          })}
        </Stack>

        {/* Grand Total */}
        <Box sx={{ mt: 3, p: 2, bgcolor: 'action.hover', borderRadius: 1 }}>
          <Stack direction="row" justifyContent="space-between" alignItems="center">
            <Typography variant="subtitle1">
              Total Across All Annotators
            </Typography>
            <Typography variant="h6">
              {totalAcrossAll.toLocaleString()} / {maxPossible.toLocaleString()} samples
            </Typography>
          </Stack>
          <LinearProgress
            variant="determinate"
            value={(totalAcrossAll / maxPossible) * 100}
            sx={{ mt: 1 }}
          />
        </Box>

        {/* Save Button */}
        <Box sx={{ mt: 3, display: 'flex', justifyContent: 'flex-end' }}>
          <Button
            variant="contained"
            startIcon={
              loading.saving ? (
                <CircularProgress size={16} color="inherit" />
              ) : (
                <SaveIcon />
              )
            }
            onClick={handleSave}
            disabled={!hasChanges || loading.saving}
          >
            Save Configuration
          </Button>
        </Box>

        {errors.settings && (
          <Typography variant="body2" color="error" sx={{ mt: 2 }}>
            Error: {errors.settings}
          </Typography>
        )}
      </CardContent>
    </Card>
  );
};

export default SampleLimitSliders;
