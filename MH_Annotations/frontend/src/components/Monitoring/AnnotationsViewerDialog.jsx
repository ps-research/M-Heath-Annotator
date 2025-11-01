import React, { useEffect, useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Box,
  Typography,
  CircularProgress,
  Alert,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  IconButton,
  Collapse,
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
} from '@mui/icons-material';
import { dataAPI } from '../../services/api';

const AnnotationRow = ({ annotation }) => {
  const [expanded, setExpanded] = useState(false);

  return (
    <>
      <TableRow hover>
        <TableCell>
          <IconButton size="small" onClick={() => setExpanded(!expanded)}>
            {expanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
          </IconButton>
        </TableCell>
        <TableCell>{annotation.id}</TableCell>
        <TableCell>
          <Chip
            label={annotation.label || 'N/A'}
            color={annotation.malformed ? 'error' : 'success'}
            size="small"
          />
        </TableCell>
        <TableCell>{annotation.malformed ? 'Yes' : 'No'}</TableCell>
        <TableCell>
          {annotation.text ? annotation.text.substring(0, 50) + '...' : 'N/A'}
        </TableCell>
      </TableRow>
      <TableRow>
        <TableCell style={{ paddingBottom: 0, paddingTop: 0 }} colSpan={5}>
          <Collapse in={expanded} timeout="auto" unmountOnExit>
            <Box sx={{ margin: 2 }}>
              {/* Request/Input */}
              <Box mb={2}>
                <Typography variant="subtitle2" gutterBottom sx={{ fontWeight: 'bold' }}>
                  Input Text:
                </Typography>
                <Paper
                  sx={{
                    p: 2,
                    backgroundColor: '#1e1e1e',
                    color: '#d4d4d4',
                    fontFamily: 'Consolas, Monaco, "Courier New", monospace',
                    fontSize: '0.875rem',
                    lineHeight: 1.6,
                    overflow: 'auto',
                    maxHeight: '200px',
                  }}
                >
                  <pre style={{ margin: 0, whiteSpace: 'pre-wrap', wordWrap: 'break-word' }}>
                    {annotation.text || 'No input text'}
                  </pre>
                </Paper>
              </Box>

              {/* Response */}
              <Box mb={2}>
                <Typography variant="subtitle2" gutterBottom sx={{ fontWeight: 'bold' }}>
                  Model Response:
                </Typography>
                <Paper
                  sx={{
                    p: 2,
                    backgroundColor: '#1e1e1e',
                    color: '#d4d4d4',
                    fontFamily: 'Consolas, Monaco, "Courier New", monospace',
                    fontSize: '0.875rem',
                    lineHeight: 1.6,
                    overflow: 'auto',
                    maxHeight: '200px',
                  }}
                >
                  <pre style={{ margin: 0, whiteSpace: 'pre-wrap', wordWrap: 'break-word' }}>
                    {annotation.response || 'No response'}
                  </pre>
                </Paper>
              </Box>

              {/* Parsed Label */}
              <Box mb={2}>
                <Typography variant="subtitle2" gutterBottom sx={{ fontWeight: 'bold' }}>
                  Parsed Label:
                </Typography>
                <Paper
                  sx={{
                    p: 2,
                    backgroundColor: annotation.malformed ? '#3a1e1e' : '#1e3a1e',
                  }}
                >
                  <Typography
                    sx={{
                      fontFamily: 'Consolas, Monaco, "Courier New", monospace',
                      color: annotation.malformed ? '#ff6b6b' : '#69db7c',
                    }}
                  >
                    {annotation.label || 'UNKNOWN'}
                  </Typography>
                </Paper>
              </Box>

              {/* Errors (if any) */}
              {(annotation.parsing_error || annotation.validity_error) && (
                <Box>
                  <Typography variant="subtitle2" gutterBottom sx={{ fontWeight: 'bold' }}>
                    Errors:
                  </Typography>
                  <Paper sx={{ p: 2, backgroundColor: '#3a1e1e' }}>
                    {annotation.parsing_error && (
                      <Typography
                        variant="body2"
                        sx={{ color: '#ff6b6b', mb: 1, fontFamily: 'monospace' }}
                      >
                        Parsing Error: {annotation.parsing_error}
                      </Typography>
                    )}
                    {annotation.validity_error && (
                      <Typography
                        variant="body2"
                        sx={{ color: '#ff6b6b', fontFamily: 'monospace' }}
                      >
                        Validity Error: {annotation.validity_error}
                      </Typography>
                    )}
                  </Paper>
                </Box>
              )}

              {/* Metadata */}
              <Box mt={2}>
                <Typography variant="caption" color="text.secondary">
                  Timestamp: {annotation.timestamp || 'N/A'}
                </Typography>
              </Box>
            </Box>
          </Collapse>
        </TableCell>
      </TableRow>
    </>
  );
};

const AnnotationsViewerDialog = ({ open, onClose, worker }) => {
  const [annotations, setAnnotations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (open && worker) {
      loadAnnotations();
    }
  }, [open, worker]);

  const loadAnnotations = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await dataAPI.getWorkerAnnotations(worker.annotator_id, worker.domain, 100);
      setAnnotations(data.annotations || []);
    } catch (err) {
      setError(err.message);
      setAnnotations([]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="lg" fullWidth>
      <DialogTitle>
        Annotations - Annotator {worker?.annotator_id} - {worker?.domain}
      </DialogTitle>
      <DialogContent>
        {loading ? (
          <Box display="flex" justifyContent="center" alignItems="center" minHeight="200px">
            <CircularProgress />
          </Box>
        ) : error ? (
          <Alert severity="error">{error}</Alert>
        ) : annotations.length === 0 ? (
          <Alert severity="info">No annotations found for this worker yet</Alert>
        ) : (
          <>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              Showing {annotations.length} annotation(s). Click row to expand and view details.
            </Typography>
            <TableContainer component={Paper} sx={{ maxHeight: '600px' }}>
              <Table stickyHeader>
                <TableHead>
                  <TableRow>
                    <TableCell width="50px"></TableCell>
                    <TableCell>Sample ID</TableCell>
                    <TableCell>Label</TableCell>
                    <TableCell>Malformed</TableCell>
                    <TableCell>Text Preview</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {annotations.map((annotation, index) => (
                    <AnnotationRow key={annotation.id || index} annotation={annotation} />
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Close</Button>
      </DialogActions>
    </Dialog>
  );
};

export default AnnotationsViewerDialog;
